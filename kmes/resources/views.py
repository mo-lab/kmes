# from django.views import generic
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib import messages
# from django.shortcuts import render, redirect, get_object_or_404
# from django.urls import reverse, reverse_lazy
# from django.utils import timezone
# from django.db import transaction
#
# from ..resources.models import (
# 	Employee, Certification, Timesheet,
# 	ToolPlant, ToolAssignment
# 	)
# from ..resources.forms import (
# 	EmployeeForm, CertificationForm, TimesheetForm,
# 	TimesheetBulkCreateForm, ToolPlantForm, ToolAssignmentForm,
# 	ToolPlantMaintenanceForm
# 	)
# from ..base_views import BaseCreateView, BaseUpdateView, BaseDeleteView
#
#
# # ============================================
# # EMPLOYEE VIEWS
# # ============================================
#
# class EmployeeListView(LoginRequiredMixin, generic.ListView):
# 	model = Employee
# 	template_name = 'resources/employee_list.html'
# 	context_object_name = 'employees'
# 	paginate_by = 30
#
# 	def get_queryset(self):
# 		queryset = Employee.objects.all()
# 		search = self.request.GET.get('search')
# 		if search:
# 			from django.db.models import Q
# 			queryset = queryset.filter(
# 					Q(first_name__icontains=search) |
# 					Q(last_name__icontains=search) |
# 					Q(employee_id__icontains=search) |
# 					Q(company__icontains=search)
# 					)
# 		trade = self.request.GET.get('trade')
# 		if trade:
# 			queryset = queryset.filter(trade=trade)
# 		is_active = self.request.GET.get('is_active')
# 		if is_active:
# 			queryset = queryset.filter(is_active=(is_active == 'true'))
# 		return queryset
#
#
# class EmployeeCreateView(BaseCreateView):
# 	model = Employee
# 	form_class = EmployeeForm
# 	template_name = 'resources/employee_form.html'
# 	success_message = "Employee '%(first_name)s %(last_name)s' was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:employee_list')
#
#
# class EmployeeUpdateView(BaseUpdateView):
# 	model = Employee
# 	form_class = EmployeeForm
# 	template_name = 'resources/employee_form.html'
# 	success_message = "Employee '%(first_name)s %(last_name)s' was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:employee_list')
#
#
# class EmployeeDeleteView(BaseDeleteView):
# 	model = Employee
# 	template_name = 'resources/employee_confirm_delete.html'
# 	success_url = reverse_lazy('resources:employee_list')
# 	success_message = "Employee was deleted successfully."
#
#
# # ============================================
# # CERTIFICATION VIEWS
# # ============================================
#
# class CertificationCreateView(BaseCreateView):
# 	model = Certification
# 	form_class = CertificationForm
# 	template_name = 'resources/certification_form.html'
# 	success_message = "Certification was added successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:employee_list')
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		employee_id = self.kwargs.get('employee_id')
# 		if employee_id:
# 			initial['employee'] = get_object_or_404(Employee, pk=employee_id)
# 		return initial
#
#
# class CertificationUpdateView(BaseUpdateView):
# 	model = Certification
# 	form_class = CertificationForm
# 	template_name = 'resources/certification_form.html'
# 	success_message = "Certification was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:employee_list')
#
#
# class CertificationDeleteView(BaseDeleteView):
# 	model = Certification
# 	template_name = 'resources/certification_confirm_delete.html'
# 	success_message = "Certification was deleted successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:employee_list')
#
#
# # ============================================
# # TIMESHEET VIEWS
# # ============================================
#
# class TimesheetListView(LoginRequiredMixin, generic.ListView):
# 	model = Timesheet
# 	template_name = 'resources/timesheet_list.html'
# 	context_object_name = 'resources:timesheets'
# 	paginate_by = 50
#
# 	def get_queryset(self):
# 		queryset = Timesheet.objects.select_related('employee', 'work_package')
# 		employee_id = self.request.GET.get('employee')
# 		if employee_id:
# 			queryset = queryset.filter(employee_id=employee_id)
# 		work_package_id = self.request.GET.get('work_package')
# 		if work_package_id:
# 			queryset = queryset.filter(work_package_id=work_package_id)
# 		date_from = self.request.GET.get('date_from')
# 		if date_from:
# 			queryset = queryset.filter(date__gte=date_from)
# 		date_to = self.request.GET.get('date_to')
# 		if date_to:
# 			queryset = queryset.filter(date__lte=date_to)
# 		return queryset.order_by('-date', 'employee__last_name')
#
#
# class TimesheetCreateView(BaseCreateView):
# 	model = Timesheet
# 	form_class = TimesheetForm
# 	template_name = 'resources/timesheet_form.html'
# 	success_message = "Timesheet entry was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:timesheet_list')
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		initial['date'] = timezone.now().date()
# 		employee_id = self.kwargs.get('employee_id')
# 		if employee_id:
# 			initial['employee'] = get_object_or_404(Employee, pk=employee_id)
# 		work_package_id = self.request.GET.get('work_package')
# 		if work_package_id:
# 			from ..construction.models import WorkPackage
# 			initial['work_package'] = get_object_or_404(WorkPackage, pk=work_package_id)
# 		return initial
#
#
# class TimesheetUpdateView(BaseUpdateView):
# 	model = Timesheet
# 	form_class = TimesheetForm
# 	template_name = 'resources/timesheet_form.html'
# 	success_message = "Timesheet entry was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:timesheet_list')
#
#
# class TimesheetDeleteView(BaseDeleteView):
# 	model = Timesheet
# 	template_name = 'resources/timesheet_confirm_delete.html'
# 	success_message = "Timesheet entry was deleted successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:timesheet_list')
#
#
# def timesheet_bulk_create_view(request):
# 	"""Bulk create timesheets for multiple employees."""
# 	if request.method == 'POST':
# 		form = TimesheetBulkCreateForm(request.POST)
# 		if form.is_valid():
# 			data = form.cleaned_data
# 			work_package = data['work_package']
# 			date = data['date']
# 			employees = data['employees']
# 			default_hours = data['default_hours']
# 			overtime_hours = data.get('overtime_hours', 0)
#
# 			created_count = 0
# 			with transaction.atomic():
# 				for employee in employees:
# 					# Check if timesheet already exists
# 					if not Timesheet.objects.filter(
# 							employee=employee,
# 							work_package=work_package,
# 							date=date
# 							).exists():
# 						Timesheet.objects.create(
# 								employee=employee,
# 								work_package=work_package,
# 								date=date,
# 								hours_worked=default_hours,
# 								overtime_hours=overtime_hours
# 								)
# 						created_count += 1
#
# 			messages.success(request, f"Successfully created {created_count} timesheet entries.")
# 			return redirect('resources:timesheet_list')
# 	else:
# 		form = TimesheetBulkCreateForm()
#
# 	return render(request, 'resources/timesheet_bulk_create.html', {'form': form})
#
#
# # ============================================
# # TOOL/PLANT VIEWS
# # ============================================
#
# class ToolPlantListView(LoginRequiredMixin, generic.ListView):
# 	model = ToolPlant
# 	template_name = 'resources/tool_plant_list.html'
# 	context_object_name = 'tools'
# 	paginate_by = 20
#
# 	def get_queryset(self):
# 		queryset = ToolPlant.objects.all()
# 		tool_type = self.request.GET.get('tool_type')
# 		if tool_type:
# 			queryset = queryset.filter(tool_type=tool_type)
# 		status = self.request.GET.get('status')
# 		if status:
# 			queryset = queryset.filter(status=status)
# 		return queryset
#
#
# class ToolPlantCreateView(BaseCreateView):
# 	model = ToolPlant
# 	form_class = ToolPlantForm
# 	template_name = 'resources/tool_plant_form.html'
# 	success_message = "Tool/Plant '%(asset_number)s' was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:tool_plant_list')
#
#
# class ToolPlantUpdateView(BaseUpdateView):
# 	model = ToolPlant
# 	form_class = ToolPlantForm
# 	template_name = 'resources/tool_plant_form.html'
# 	success_message = "Tool/Plant '%(asset_number)s' was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('resources:tool_plant_list')
#
#
# class ToolPlantDeleteView(BaseDeleteView):
# 	model = ToolPlant
# 	template_name = 'resources/tool_plant_confirm_delete.html'
# 	success_url = reverse_lazy('resources:tool_plant_list')
# 	success_message = "Tool/Plant was deleted successfully."
#
#
# def tool_plant_maintenance_view(request, pk):
# 	"""Update maintenance status of a tool/plant."""
# 	tool = get_object_or_404(ToolPlant, pk=pk)
#
# 	if request.method == 'POST':
# 		form = ToolPlantMaintenanceForm(request.POST, instance=tool)
# 		if form.is_valid():
# 			form.save()
# 			messages.success(request, f"Maintenance updated for {tool.asset_number}.")
# 			return redirect('resources:tool_plant_list')
# 	else:
# 		form = ToolPlantMaintenanceForm(instance=tool)
#
# 	return render(request, 'resources/tool_plant_maintenance.html', {
# 			'tool': tool,
# 			'form': form,
# 			})
#
#
# # ============================================
# # TOOL ASSIGNMENT VIEWS
# # ============================================
#
# class ToolAssignmentCreateView(BaseCreateView):
# 	model = ToolAssignment
# 	form_class = ToolAssignmentForm
# 	template_name = 'resources/tool_assignment_form.html'
# 	success_message = "Tool assignment was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		initial['assignment_start'] = timezone.now()
# 		tool_id = self.kwargs.get('tool_id')
# 		if tool_id:
# 			initial['tool_plant'] = get_object_or_404(ToolPlant, pk=tool_id)
# 		work_package_id = self.request.GET.get('work_package')
# 		if work_package_id:
# 			from ..construction.models import WorkPackage
# 			initial['work_package'] = get_object_or_404(WorkPackage, pk=work_package_id)
# 		return initial
#
#
# class ToolAssignmentUpdateView(BaseUpdateView):
# 	model = ToolAssignment
# 	form_class = ToolAssignmentForm
# 	template_name = 'resources/tool_assignment_form.html'
# 	success_message = "Tool assignment was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
#
#
# class ToolAssignmentDeleteView(BaseDeleteView):
# 	model = ToolAssignment
# 	template_name = 'resources/tool_assignment_confirm_delete.html'
# 	success_message = "Tool assignment was deleted successfully."
#
# 	def get_success_url(self):
# 		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})