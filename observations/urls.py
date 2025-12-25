# observations/urls.py
from django.urls import path
from . import views

app_name = 'observations'

urlpatterns = [
    path('', views.observation_list, name='observation_list'),
    path('new/', views.ObservationCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ObservationDetailView.as_view(), name='detail'),
    path('<int:pk>/rectify/', views.RectificationUpdateView.as_view(), name='rectify'),
    path('<int:pk>/verify/', views.VerificationView.as_view(), name='verify'),

    # Archiving URLs
    path('<int:pk>/archive/', views.archive_observation, name='archive'),
    path('<int:pk>/restore/', views.restore_observation, name='restore'),
    path('archived/', views.archived_observations_list, name='archived_list'),

    # Export URLs
    path('export/csv/', views.export_observations_csv, name='export_observations_csv'),
    path('export/excel/', views.export_observations_excel, name='export_observations_excel'),
    path('ajax/add-location/', views.ajax_add_location, name='ajax_add_location'),

    # delete observation
    path('<int:pk>/delete/', views.delete_observation, name='delete'),

    # Dashboard URL
    path('dashboard/', views.observations_dashboard, name='dashboard'),


]

