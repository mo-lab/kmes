# # your_app/urls/resources.py
# from django.urls import path
# from .views import *
#
# app_name = 'resources'
#
# urlpatterns = [
# 		# ============================================
# 		# EMPLOYEE URLS
# 		# ============================================
# 		path(
# 			'employees/',
# 			EmployeeListView.as_view(),
# 			name='employee_list'
# 			),
#
# 		path(
# 			'employees/create/',
# 			EmployeeCreateView.as_view(),
# 			name='employee_create'
# 			),
#
# 		path(
# 			'employees/<int:pk>/update/',
# 			EmployeeUpdateView.as_view(),
# 			name='employee_update'
# 			),
#
# 		path(
# 			'employees/<int:pk>/delete/',
# 			EmployeeDeleteView.as_view(),
# 			name='employee_delete'
# 			),
#
# 		# ============================================
# 		# CERTIFICATION URLS
# 		# ============================================
# 		path(
# 			'employees/<int:employee_id>/certifications/create/',
# 			CertificationCreateView.as_view(),
# 			name='certification_create'
# 			),
#
# 		path(
# 			'certifications/<int:pk>/update/',
# 			CertificationUpdateView.as_view(),
# 			name='certification_update'
# 			),
#
# 		path(
# 			'certifications/<int:pk>/delete/',
# 			CertificationDeleteView.as_view(),
# 			name='certification_delete'
# 			),
#
# 		# ============================================
# 		# TIMESHEET URLS
# 		# ============================================
# 		path(
# 			'timesheets/',
# 			TimesheetListView.as_view(),
# 			name='timesheet_list'
# 			),
#
# 		path(
# 			'timesheets/create/',
# 			TimesheetCreateView.as_view(),
# 			name='timesheet_create'
# 			),
#
# 		path(
# 			'timesheets/create/employee/<int:employee_id>/',
# 			TimesheetCreateView.as_view(),
# 			name='timesheet_create_for_employee'
# 			),
#
# 		path(
# 			'timesheets/<int:pk>/update/',
# 			TimesheetUpdateView.as_view(),
# 			name='timesheet_update'
# 			),
#
# 		path(
# 			'timesheets/<int:pk>/delete/',
# 			TimesheetDeleteView.as_view(),
# 			name='timesheet_delete'
# 			),
#
# 		path(
# 			'timesheets/bulk-create/',
# 			timesheet_bulk_create_view,
# 			name='timesheet_bulk_create'
# 			),
#
# 		# ============================================
# 		# TOOL/PLANT URLS
# 		# ============================================
# 		path(
# 			'tools/',
# 			ToolPlantListView.as_view(),
# 			name='tool_plant_list'
# 			),
#
# 		path(
# 			'tools/create/',
# 			ToolPlantCreateView.as_view(),
# 			name='tool_plant_create'
# 			),
#
# 		path(
# 			'tools/<int:pk>/update/',
# 			ToolPlantUpdateView.as_view(),
# 			name='tool_plant_update'
# 			),
#
# 		path(
# 			'tools/<int:pk>/delete/',
# 			ToolPlantDeleteView.as_view(),
# 			name='tool_plant_delete'
# 			),
#
# 		path(
# 			'tools/<int:pk>/maintenance/',
# 			tool_plant_maintenance_view,
# 			name='tool_plant_maintenance'
# 			),
#
# 		# ============================================
# 		# TOOL ASSIGNMENT URLS
# 		# ============================================
# 		path(
# 			'tool-assignments/create/',
# 			ToolAssignmentCreateView.as_view(),
# 			name='tool_assignment_create'
# 			),
#
# 		path(
# 			'tool-assignments/create/tool/<int:tool_id>/',
# 			ToolAssignmentCreateView.as_view(),
# 			name='tool_assignment_create_for_tool'
# 			),
#
# 		path(
# 			'tool-assignments/<int:pk>/update/',
# 			ToolAssignmentUpdateView.as_view(),
# 			name='tool_assignment_update'
# 			),
#
# 		path(
# 			'tool-assignments/<int:pk>/delete/',
# 			ToolAssignmentDeleteView.as_view(),
# 			name='tool_assignment_delete'
# 			),
# 		]
