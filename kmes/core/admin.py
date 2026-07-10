from django.contrib import admin
from .models import Project, Area, System, EquipmentTag

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = ['name', 'code', 'location', 'status', 'start_date', 'target_completion_date']
	list_filter = ['status']
	search_fields = ['name', 'code', 'location']

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'project']
	list_filter = ['project']
	search_fields = ['code', 'name']

@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'project']
	list_filter = ['project']
	search_fields = ['code', 'name']

@admin.register(EquipmentTag)
class EquipmentTagAdmin(admin.ModelAdmin):
	list_display = ['tag_number', 'description', 'equipment_type', 'status', 'project', 'area']
	list_filter = ['equipment_type', 'status', 'discipline', 'project']
	search_fields = ['tag_number', 'description']