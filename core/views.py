from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import DemoRequestForm

# Create your views here.
def home_view(request):
    """Lightweight marketing-style homepage"""
    return render(request, "home.html", {})


def request_demo_view(request):
    if request.method == "POST":
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thank you! Our team will contact you shortly to schedule the demo."
            )
            return redirect("home")
    else:
        form = DemoRequestForm()

    return render(request, "request_demo.html", {"form": form})
