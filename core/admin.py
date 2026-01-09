from django.contrib import admin

# Register your models here.
from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import DemoRequest

@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "company", "email","whatsapp_number", "created_at", "message")
    search_fields = ("full_name", "email", "company")
