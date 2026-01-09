from django.db import models

# Create your models here.

from django.db import models

class DemoRequest(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    whatsapp_number = models.CharField(max_length=20)
    company = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.company})"
