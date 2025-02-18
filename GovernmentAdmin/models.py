from django.db import models

from users.models import GovernmentAdmin


# Create your models here.
class Ministry(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    admin = models.OneToOneField(GovernmentAdmin, on_delete=models.SET_NULL, null=True, related_name="managed_ministry")
    kpi_resolved = models.IntegerField(default=0)
    kpi_pending = models.IntegerField(default=0)
    kpi_rejected = models.IntegerField(default=0)

    def update_kpis(self):
        self.kpi_resolved = self.reports.filter(status="Resolved").count()
        self.kpi_pending = self.reports.filter(status="Pending").count()
        self.kpi_rejected = self.reports.filter(status="Rejected").count()
        self.save()

    def __str__(self):
        return self.name

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _



