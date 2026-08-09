from django.contrib import admin
from .models import Employee, Certification, Timesheet, ToolPlant, ToolAssignment, Company


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
	list_display = ['employee_id', 'first_name', 'last_name', 'company', 'trade', 'is_active']
	list_filter = ['trade', 'company', 'is_active']
	search_fields = ['first_name', 'last_name', 'employee_id', 'company']

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
	list_display = ['employee', 'name', 'issue_date', 'expiry_date', 'is_valid']
	list_filter = ['is_valid']
	search_fields = ['name', 'employee__first_name', 'employee__last_name']

@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
	list_display = ['employee', 'work_package', 'date', 'hours_worked', 'overtime_hours']
	list_filter = ['date']
	search_fields = ['employee__first_name', 'employee__last_name']

@admin.register(ToolPlant)
class ToolPlantAdmin(admin.ModelAdmin):
	list_display = ['asset_number', 'tool_type', 'make', 'model', 'status']
	list_filter = ['tool_type', 'status']
	search_fields = ['asset_number', 'make', 'model']

@admin.register(ToolAssignment)
class ToolAssignmentAdmin(admin.ModelAdmin):
	list_display = ['tool_plant', 'work_package', 'assignment_start', 'assignment_end']
	list_filter = ['assignment_start']
	
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
	list_display = ['title']
	search_fields = ['title']
	list_filter = ['title']