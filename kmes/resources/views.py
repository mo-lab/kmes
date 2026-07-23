from datetime import timedelta

from django.forms import CharField
from django.utils import timezone
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.db.models import Q, Count, Sum, When
from django.contrib.auth import get_user_model
from sqlparse.sql import Case

from .models import Employee, Certification, Timesheet
from .forms import EmployeeForm, EmployeeSearchForm


User = get_user_model()


class EmployeeCreateView(LoginRequiredMixin, generic.CreateView):
	"""Create a new employee record."""
	model = Employee
	form_class = EmployeeForm
	template_name = 'resources/employee_form.html'
	success_message = "Employee '%(first_name)s %(last_name)s' was created successfully."
	
	def get_success_url(self):
		if self.request.POST.get('save_add_another'):
			return reverse('resources:employee_create')
		return reverse('resources:employee_list')
	
	def get_initial(self):
		initial = super().get_initial()
		
		# Pre-fill from URL parameters
		company = self.request.GET.get('company')
		if company:
			initial['company'] = company
		
		trade = self.request.GET.get('trade')
		if trade:
			initial['trade'] = trade
		
		# Set defaults
		initial['is_active'] = True
		initial['hire_date'] = timezone.now().date()
		
		# Auto-generate employee ID
		initial['employee_id'] = self.generate_employee_id()
		
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = True
		context['page_title'] = 'Add New Employee'
		
		# Recent employees for reference
		context['recent_employees'] = Employee.objects.order_by('-created_at')[:5]
		
		# Trade statistics
		context['trade_stats'] = Employee.objects.values('trade').annotate(
				count=Count('id')
				).order_by('trade')
		
		# Company list for autocomplete
		context['companies'] = Employee.objects.values_list(
				'company', flat=True
				).distinct().order_by('company')
		
		return context
	
	def form_valid(self, form):
		# Check if employee ID already exists
		employee_id = form.cleaned_data.get('employee_id')
		if Employee.objects.filter(employee_id=employee_id).exists():
			messages.warning(
					self.request,
					f'Employee ID "{employee_id}" already exists. A new ID will be generated.'
					)
			form.instance.employee_id = self.generate_employee_id()
		
		# Check if user account already linked
		if form.cleaned_data.get('user'):
			existing = Employee.objects.filter(user=form.cleaned_data['user']).first()
			if existing and existing.pk != (self.object.pk if self.object else None):
				messages.warning(
						self.request,
						f'User account is already linked to employee "{existing.full_name}".'
						)
				form.instance.user = None
		
		messages.success(
				self.request,
				self.success_message % {
						'first_name': form.cleaned_data['first_name'],
						'last_name': form.cleaned_data['last_name']
						}
				)
		
		return super().form_valid(form)
	
	def form_invalid(self, form):
		messages.error(self.request, 'Please correct the errors below.')
		return super().form_invalid(form)
	
	def generate_employee_id(self):
		"""Generate a unique employee ID."""
		prefix = 'EMP'
		year = timezone.now().strftime('%y')
		
		# Find the latest employee ID
		last_employee = Employee.objects.filter(
				employee_id__startswith=f'{prefix}-{year}'
				).order_by('-employee_id').first()
		
		if last_employee:
			try:
				last_num = int(last_employee.employee_id.split('-')[-1])
				new_num = last_num + 1
			except (ValueError, IndexError):
				new_num = 1
		else:
			new_num = 1
		
		return f'{prefix}-{year}-{new_num:04d}'


class EmployeeUpdateView(LoginRequiredMixin, generic.UpdateView):
	"""Update an existing employee record."""
	model = Employee
	form_class = EmployeeForm
	template_name = 'resources/employee_form.html'
	success_message = "Employee '%(first_name)s %(last_name)s' was updated successfully."
	
	def get_success_url(self):
		return reverse('resources:employee_list')
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = False
		context['page_title'] = f'Edit Employee: {self.object.full_name}'
		
		# Get employee's certifications
		context['certifications'] = self.object.certifications.all().order_by('-expiry_date')
		
		# Get employee's timesheet summary
		context['timesheet_summary'] = self.object.timesheets.aggregate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				total_days=Count('date', distinct=True)
				)
		
		# Get recent timesheets
		context['recent_timesheets'] = self.object.timesheets.select_related(
				'work_package'
				).order_by('-date')[:10]
		
		return context
	
	def form_valid(self, form):
		# Track changes
		old_instance = Employee.objects.get(pk=self.object.pk)
		
		messages.success(
				self.request,
				self.success_message % {
						'first_name': form.cleaned_data['first_name'],
						'last_name': form.cleaned_data['last_name']
						}
				)
		
		return super().form_valid(form)


class EmployeeDeleteView(LoginRequiredMixin, generic.DeleteView):
	"""Delete an employee record."""
	model = Employee
	template_name = 'resources/employee_confirm_delete.html'
	success_url = reverse_lazy('resources:employee_list')
	success_message = "Employee was deleted successfully."
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		employee = self.get_object()
		context['has_timesheets'] = employee.timesheets.exists()
		context['has_certifications'] = employee.certifications.exists()
		return context
	
	def delete(self, request, *args, **kwargs):
		employee = self.get_object()
		messages.success(
				request,
				f'Employee "{employee.full_name}" was deleted successfully.'
				)
		return super().delete(request, *args, **kwargs)


class EmployeeListView(LoginRequiredMixin, generic.ListView):
	model = Employee
	template_name = 'resources/employee_list.html'
	context_object_name = 'employees'
	paginate_by = 30
	
	def get_queryset(self):
		queryset = Employee.objects.select_related('user').annotate(
				certification_count=Count('certifications', distinct=True),
				# valid_certification_count=Count(
				# 		Case(
				# 				When(
				# 						certifications__is_valid=True,
				# 						certifications__expiry_date__gte=timezone.now().date(),
				# 						then=1
				# 						),
				# 				output_field=CharField(),
				# 				),
				# 		distinct=True
				# 		),
				# expired_certification_count=Count(
				# 		Case(
				# 				When(
				# 						Q(certifications__is_valid=False) |
				# 						Q(certifications__expiry_date__lt=timezone.now().date()),
				# 						then=1
				# 						),
				# 				output_field=CharField(),
				# 				),
				# 		distinct=True
				# 		),
				timesheet_count=Count('timesheets', distinct=True),
				total_hours=Sum('timesheets__hours_worked'),
				total_overtime=Sum('timesheets__overtime_hours'),
				)
		
		# Apply filters
		form = EmployeeSearchForm(self.request.GET)
		if form.is_valid():
			data = form.cleaned_data
			
			if data.get('search'):
				search = data['search']
				queryset = queryset.filter(
						Q(first_name__icontains=search) |
						Q(last_name__icontains=search) |
						Q(employee_id__icontains=search) |
						Q(company__icontains=search) |
						Q(email__icontains=search) |
						Q(phone__icontains=search)
						)
			
			if data.get('trade'):
				queryset = queryset.filter(trade=data['trade'])
			
			if data.get('company'):
				queryset = queryset.filter(company__icontains=data['company'])
			
			if data.get('is_active') in ['true', 'false']:
				queryset = queryset.filter(is_active=data['is_active'] == 'true')
			
			if data.get('has_certifications') == 'true':
				queryset = queryset.filter(certification_count__gt=0)
			
			if data.get('has_expired_certs') == 'true':
				queryset = queryset.filter(expired_certification_count__gt=0)
		
		# Apply sorting
		sort = self.request.GET.get('sort', 'last_name')
		allowed_sorts = [
				'first_name', '-first_name',
				'last_name', '-last_name',
				'employee_id', '-employee_id',
				'company', '-company',
				'trade', '-trade',
				'hire_date', '-hire_date',
				'certification_count', '-certification_count',
				'total_hours', '-total_hours',
				]
		if sort in allowed_sorts:
			queryset = queryset.order_by(sort)
		
		return queryset
	
	def get_paginate_by(self, queryset):
		per_page = self.request.GET.get('per_page', '30')
		try:
			return min(int(per_page), 100)
		except ValueError:
			return 30
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Search form
		context['search_form'] = EmployeeSearchForm(self.request.GET)
		
		# View mode
		context['view_mode'] = self.request.GET.get('view', 'table')
		
		# Statistics
		base_queryset = Employee.objects.all()
		
		context['total_employees'] = base_queryset.count()
		context['active_employees'] = base_queryset.filter(is_active=True).count()
		context['inactive_employees'] = base_queryset.filter(is_active=False).count()
		
		# Certification stats
		context['employees_with_certs'] = Certification.objects.values('employee').distinct().count()
		context['expiring_certifications'] = Certification.objects.filter(
				expiry_date__lte=timezone.now().date() + timedelta(days=30),
				expiry_date__gte=timezone.now().date(),
				is_valid=True
				).select_related('employee').order_by('expiry_date')[:10]
		
		context['expired_certifications_count'] = Certification.objects.filter(
				Q(is_valid=False) | Q(expiry_date__lt=timezone.now().date())
				).count()
		
		# Trade distribution
		context['trade_distribution'] = base_queryset.values('trade').annotate(
				count=Count('id')
				).order_by('-count')
		
		# Company distribution
		context['company_distribution'] = base_queryset.values('company').annotate(
				count=Count('id'),
				total_hours=Sum('timesheets__hours_worked')
				).order_by('-count')[:10]
		
		# Recent hires (last 30 days)
		thirty_days_ago = timezone.now().date() - timedelta(days=30)
		context['recent_hires'] = base_queryset.filter(
				hire_date__gte=thirty_days_ago
				).count()
		
		# Total hours this month
		month_start = timezone.now().date().replace(day=1)
		context['month_total_hours'] = Timesheet.objects.filter(
				date__gte=month_start
				).aggregate(total=Sum('hours_worked'))['total'] or 0
		
		# Companies for filter dropdown
		context['companies'] = base_queryset.values_list(
				'company', flat=True
				).distinct().order_by('company')
		
		# Current date
		context['today'] = timezone.now().date()
		
		return context

class EmployeeDetailView(LoginRequiredMixin, generic.DetailView):
	"""View employee details."""
	model = Employee
	template_name = 'resources/employee_detail.html'
	context_object_name = 'employee'
	
	def get_queryset(self):
		return Employee.objects.select_related('user').prefetch_related(
				'certifications',
				'timesheets__work_package'
				)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		employee = self.get_object()
		
		# Certifications
		context['certifications'] = employee.certifications.all().order_by('-expiry_date')
		context['valid_certifications'] = employee.certifications.filter(
				is_valid=True,
				expiry_date__gte=timezone.now().date()
				).count()
		context['expired_certifications'] = employee.certifications.filter(
				Q(is_valid=False) | Q(expiry_date__lt=timezone.now().date())
				).count()
		
		# Timesheet summary
		timesheet_data = employee.timesheets.aggregate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				total_days=Count('date', distinct=True)
				)
		context['timesheet_summary'] = timesheet_data
		
		# Recent timesheets
		context['recent_timesheets'] = employee.timesheets.select_related(
				'work_package__project'
				).order_by('-date')[:20]
		
		# Work package history
		context['work_packages'] = employee.timesheets.values(
				'work_package__code',
				'work_package__name',
				'work_package_id'
				).annotate(
				total_hours=Sum('hours_worked'),
				days_worked=Count('date', distinct=True)
				).order_by('-days_worked')[:10]
		
		return context