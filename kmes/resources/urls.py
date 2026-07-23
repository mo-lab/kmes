# your_app/urls/resources.py
from django.urls import path
from .views import EmployeeCreateView, EmployeeListView

app_name = 'resources'

urlpatterns = [
		path('employees/create/', EmployeeCreateView.as_view(), name='employee_create'),
		path('employees/', EmployeeListView.as_view(), name='employee_list'),

			]
