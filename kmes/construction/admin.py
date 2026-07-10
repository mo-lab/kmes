from django.contrib import admin
from .models import WorkPackage, WorkPackageItem, DailyProgressReport, InstalledItemCheck

@admin.register(WorkPackage)
class WorkPackageAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'area', 'status', 'planned_start', 'planned_finish', 'percent_complete']
	list_filter = ['status', 'project']
	search_fields = ['code', 'name']

@admin.register(WorkPackageItem)
class WorkPackageItemAdmin(admin.ModelAdmin):
	list_display = ['work_package', 'equipment_tag', 'sequence_number', 'is_complete']
	list_filter = ['is_complete']

@admin.register(DailyProgressReport)
class DailyProgressReportAdmin(admin.ModelAdmin):
	list_display = ['work_package', 'report_date', 'reported_by', 'manpower_count']
	list_filter = ['report_date']

@admin.register(InstalledItemCheck)
class InstalledItemCheckAdmin(admin.ModelAdmin):
	list_display = ['equipment_tag', 'checked_date', 'status', 'checked_by']
	list_filter = ['status', 'checked_date']