# your_app/urls/resources.py
from django.urls import path
from .views import EmployeeCreateView, EmployeeListView,EmployeeDetailView,TimesheetListView,TimesheetCreateView

app_name = 'resources'

urlpatterns = [
		path('employees/create/', EmployeeCreateView.as_view(), name='employee_create'),
		path('employees/', EmployeeListView.as_view(), name='employee_list'),
		path('employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee_detail'),
		path('timesheets/', TimesheetListView.as_view(), name='timesheet_list'),
		path('timesheets/create/', TimesheetCreateView.as_view(), name='timesheet_create'),
		
			]
