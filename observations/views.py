from django.shortcuts import render

# Create your views here.

# observations/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, UpdateView, ListView, DetailView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Observation
from .forms import ObservationCreateForm, RectificationForm, VerificationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Location
from .forms import LocationForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from datetime import date
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

# Helper mixins
class ObserverRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_observer

class IsAssignedOrManagerMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        return user.is_safety_manager or (obj.assigned_to and obj.assigned_to == user)

# Views
class ObservationCreateView(LoginRequiredMixin,  CreateView):
    #ObserverRequiredMixin,
    model = Observation
    form_class = ObservationCreateForm
    template_name = 'observations/observation_form.html'
    success_url = reverse_lazy('observations:observation_list')

    def form_valid(self, form):
        form.instance.observer = self.request.user
        form.instance.status = 'OPEN'
        return super().form_valid(form)

# Uncomment below to use class-based list view
# class ObservationListView(LoginRequiredMixin, ListView):
#     model = Observation
#     template_name = 'observations/observation_list.html'
#     context_object_name = 'observations'

#     def get_queryset(self):
#         qs = super().get_queryset().select_related('location','assigned_to')
#         q = self.request.GET.get('q')
#         if q:
#             qs = qs.filter(title__icontains=q)
#         return qs.order_by('-date_observed')

#observations list view function 
@login_required
def observation_list(request):
    #----1. handle search query-----
    q = request.GET.get('q', '').strip()
    observations = Observation.objects.filter(is_archived=False).select_related('location','assigned_to').order_by('-date_observed')

    if q:
        observations = observations.filter(
            Q(title__icontains=q) | 
            Q(description__icontains=q) |
            Q(location__name__icontains=q) |
            Q(observer__username__icontains=q)
        )
    #----2. handle pagination-----
    paginator = Paginator(observations, 10)  # Show 10 observations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'observations': page_obj,
        'page_obj': page_obj,
        'q': q, # to retain search query in template
        'today': date.today(), # to compare target_date in template
    }
    
    return render(request, 'observations/observation_list.html', context)
    # return render(request, 'observations/observation_list.html', {'observations': observations})    




class ObservationDetailView(LoginRequiredMixin, DetailView):
    model = Observation
    template_name = 'observations/observation_detail.html'

class RectificationUpdateView(LoginRequiredMixin, IsAssignedOrManagerMixin, UpdateView):
    model = Observation
    form_class = RectificationForm
    template_name = 'observations/observation_form.html'
    success_url = reverse_lazy('observations:observation_list')

    # def form_valid(self, form):
    #     form.instance.status = 'IN_PROGRESS'
    #     return super().form_valid(form)
    
    def form_valid(self, form):
        """
        When Action Owner submits the rectification:
        - Update rectification details, photo_after, target_date.
        - Change status to 'AWAITING VERIFICATION'.
        - Save the observation and redirect.
        """
        observation = form.save(commit=False)
        observation.status = 'AWAITING VERIFICATION'
        observation.save()
        messages.success(self.request, "Rectification details submitted successfully, pending for verification!.")
        return super().form_valid(form)

    def test_func(self):
        """
        Restrict access so that only the Action Owner (assigned_to)
        can access and update this observation.
        """
        observation = self.get_object()
        return self.request.user == observation.assigned_to

    # def form_valid(self, form):
    #     observation = form.save(commit=False)
    #     observation.status = 'AWAITING VERIFICATION'
    #     observation.save()
    #     messages.success(self.request, "Rectification details submitted successfully, pending for verification!.")
    #     return super().form_valid(form)



class VerificationView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Observation
    template_name = 'observations/observation_verify.html'
    form_class = VerificationForm

    def test_func(self):
        # return self.request.user.is_safety_manager
        return self.request.user.is_authenticated and self.request.user.is_safety_manager

    def dispatch(self, request, *args, **kwargs):
        self.observation = get_object_or_404(Observation, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['observation'] = self.observation
        return ctx

    def form_valid(self, form):
        observation = form.save(commit=False)
        action = form.cleaned_data.get('verification_action')

        if action == 'approve':
            observation.status = 'CLOSED'
            observation.date_closed = timezone.now()
            messages.success(self.request, "✅ Observation verified and closed successfully.")
        else:
            observation.status = 'IN PROGRESS'
            messages.warning(self.request, "⚠️ Observation sent back for rework.")

        observation.save()
        return redirect('observations:observation_list')  # redirect to your list/dashboard page


# Delete observation view

def is_superuser(user):
    return user.is_superuser
@login_required
@user_passes_test(is_superuser)

def delete_observation(request, pk):
    obs = get_object_or_404(Observation, pk=pk)

    if request.method == 'POST':
        obs.delete()
        messages.success(request, "Observation deleted successfully.")
        return redirect("observations:observation_list")
       
    return render(request, "observations/confirm_delete.html", {"observation":obs})

# View to list archived observations
@login_required
def archived_observations_list(request):
    """List all archived (closed) observations"""
    archived = Observation.objects.filter(is_archived=True).order_by('-id')

    # Handle pagination
    paginator = Paginator(archived, 10)  # Show 10 observations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'observations': page_obj,
        'page_obj': page_obj,
        'today': timezone.now().date(), # to compare target_date in template
        'is_archive_page': True,
    }
    
    return render(request, 'observations/archived_list.html', context)

def is_safety_manager(user):
    return user.groups.filter(name='Managers').exists() or user.is_superuser

@login_required
@user_passes_test(is_safety_manager)
def archive_observation(request, pk):
    obs = get_object_or_404(Observation, pk=pk)
    obs.is_archived = True
    obs.save()
    return redirect("observations:observation_list")
    # return redirect("observations:archived_list")


def restore_observation(request, pk):
    obs = get_object_or_404(Observation, pk=pk)
    obs.is_archived = False
    obs.save()
    return redirect("observations:archived_list")
    # return redirect("observations:observation_list")

from openpyxl import Workbook

def export_observations_excel(request):
    """Download all observations as Excel file"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Observations"

    headers = [
        "ID",
        "Title",
        "Description",
        "Location",
        "Status",
        "Observer",
        "Created At",
    ]
    ws.append(headers)

    for obs in Observation.objects.all().select_related("observer"):
        ws.append([
            obs.id,
            obs.title,
            obs.description,
            str(obs.location),
            obs.status,
            obs.observer.username if obs.observer else "",
            obs.date_observed.strftime("%Y-%m-%d %H:%M"),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="observations.xlsx"'

    wb.save(response)
    return response

    # observations/views.py

import csv
from django.http import HttpResponse
from .models import Observation

def export_observations_csv(request):
    """Download all observations as CSV"""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="observations.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "ID",
        "Title",
        "Description",
        "Location",
        "Status",
        "Observer",
        "Created At",
    ])

    for obs in Observation.objects.all().select_related("observer"):
        writer.writerow([
            obs.id,
            obs.title,
            obs.description,
            obs.location,
            obs.status,
            obs.observer.username if obs.observer else "",
            obs.date_observed.strftime("%Y-%m-%d %H:%M"),
        ])

    return response

# Add API endpoint to create a Location
@require_POST
def ajax_add_location(request):
    form = LocationForm(request.POST)
    if form.is_valid():
        location = form.save()
        return JsonResponse({
            "success": True,
            "id": location.id,
            "name": location.name,
        })
    else:
        return JsonResponse({
            "success": False,
            "errors": form.errors,
        })

# Dashboard view

import pandas as pd
import plotly.express as px
from plotly.io import to_image
from django.http import HttpResponse
from django.db.models import Count, Q
from django.shortcuts import render
from .models import Observation, Location
from datetime import datetime

@login_required
def observations_dashboard(request):

    # =========================================================================
    # 1. Read Filter Values
    # =========================================================================
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    location_id = request.GET.get("location")

    qs = Observation.objects.filter(is_archived=False)

    if start_date:
        qs = qs.filter(date_observed__date__gte=start_date)
    if end_date:
        qs = qs.filter(date_observed__date__lte=end_date)
    if location_id and location_id != "all":
        qs = qs.filter(location_id=location_id)

    # =========================================================================
    # 2. KPI Cards
    # =========================================================================
    total_obs = qs.count()
    open_obs = qs.filter(status="OPEN").count()
    closed_obs = qs.filter(status="CLOSED").count()
    overdue_obs = qs.filter(target_date__lt=datetime.today().date()).exclude(status="CLOSED" ).count()

    # =========================================================================
    # 3. Aggregated Data
    # =========================================================================
    severity_df = pd.DataFrame(list(qs.values("severity").annotate(total=Count("id"))))
    status_df = pd.DataFrame(list(qs.values("status").annotate(total=Count("id"))))

    monthly_df = (
        qs.extra(select={"month": "strftime('%%Y-%%m', date_observed)"})
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    monthly_df = pd.DataFrame(list(monthly_df))

    # =========================================================================
    # 4. Drill-down: If user clicks severity bar → show table
    # =========================================================================
    drill_severity = request.GET.get("drill_severity")
    drill_data = None
    if drill_severity:
        drill_data = qs.filter(severity=drill_severity)

    # =========================================================================
    # 5. Plotly Charts
    # =========================================================================

    # Severity Chart
    fig_severity = px.bar(severity_df, x="severity", y="total",
                          title="Observations by Severity")
    severity_plot = fig_severity.to_html(full_html=False)

    # Status Pie Chart
    fig_status = px.pie(status_df, names="status", values="total",
                        title="Status Distribution")
    status_plot = fig_status.to_html(full_html=False)

    # Monthly Trends
    fig_monthly = px.line(monthly_df, x="month", y="total",
                          markers=True, title="Monthly Trend")
    monthly_plot = fig_monthly.to_html(full_html=False)

    # =========================================================================
    # 6. Export PNG Feature
    # =========================================================================
    if request.GET.get("export_png"):
        fig_name = request.GET.get("export_png")
        fig_map = {
            "severity": fig_severity,
            "status": fig_status,
            "monthly": fig_monthly,
        }
        fig = fig_map.get(fig_name)
        if fig:
            png_bytes = to_image(fig, format="png")
            response = HttpResponse(png_bytes, content_type="image/png")
            response["Content-Disposition"] = f'attachment; filename="{fig_name}.png"'
            return response

    # =========================================================================
    # 7. Send to Template
    # =========================================================================
    return render(request, "observations/dashboard.html", {
        "severity_plot": severity_plot,
        "status_plot": status_plot,
        "monthly_plot": monthly_plot,

        # KPI cards
        "total_obs": total_obs,
        "open_obs": open_obs,
        "closed_obs": closed_obs,
        "overdue_obs": overdue_obs,

        # filters
        "start_date": start_date,
        "end_date": end_date,
        "location_id": location_id,
        "locations": Location.objects.all(),

        # drill-down
        "drill_severity": drill_severity,
        "drill_data": drill_data,
    })


