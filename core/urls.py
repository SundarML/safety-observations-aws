from django.urls import path
from .views import request_demo_view

urlpatterns = [
    path("request-demo/", request_demo_view, name="request_demo"),
]
