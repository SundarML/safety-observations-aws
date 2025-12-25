from django.db import models

# Create your models here.
# observations/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

class Location(models.Model):
    name = models.CharField(max_length=200)
    area = models.CharField(max_length=200, blank=True)
    facility = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.name} ({self.area})" if self.area else self.name

class Observation(models.Model):
    SEVERITY_CHOICES = [
        ('LOW','Low'),
        ('MEDIUM','Medium'),
        ('HIGH','High'),
    ]

    STATUS_CHOICES = [
        ('OPEN','Open'),
        ('IN_PROGRESS','In Progress'),
        ('AWAITING_VERIFICATION','Awaiting Verification'),
        ('CLOSED','Closed'),
    ]

    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='observations')
    observer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='observed')
    date_observed = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='LOW')
    photo_before = models.ImageField(upload_to='observations/before/', blank=True, null=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_observations')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='OPEN')
    target_date = models.DateField(null=True, blank=True)
    rectification_details = models.TextField(blank=True)
    photo_after = models.ImageField(upload_to='observations/after/', blank=True, null=True)
    date_closed = models.DateTimeField(null=True, blank=True)
    verification_comment = models.TextField(blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def close(self):
        self.status = 'CLOSED'
        self.date_closed = timezone.now()
        self.save()

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title} - {self.status}"

