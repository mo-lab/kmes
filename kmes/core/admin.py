from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.Project)
admin.site.register(models.Area)
admin.site.register(models.EquipmentTag)
admin.site.register(models.System)
