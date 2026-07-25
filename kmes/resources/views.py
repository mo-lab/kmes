from datetime import timedelta

from django.forms import CharField
from django.utils import timezone
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.db.models import Q, Count, Sum, When, Min, Max, Avg
from django.contrib.auth import get_user_model
from sqlparse.sql import Case
from construction.models import WorkPackage
from .models import Employee, Certification, Timesheet
from .forms import EmployeeForm, EmployeeSearchForm, TimesheetSearchForm, TimesheetBulkForm, TimesheetForm

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




class EmployeeDetailView(LoginRequiredMixin, generic.DetailView):
	"""View employee details with certifications, timesheets, and work history."""
	model = Employee
	template_name = 'resources/employee_detail.html'
	context_object_name = 'employee'
	
	def get_queryset(self):
		return Employee.objects.select_related('user').prefetch_related(
				'certifications',
				'timesheets__work_package__project',
				'timesheets__work_package__area'
				)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		employee = self.get_object()
		
		# Certifications
		certifications = employee.certifications.all().order_by('-expiry_date')
		context['certifications'] = certifications
		
		context['valid_certifications'] = certifications.filter(
				is_valid=True,
				expiry_date__gte=timezone.now().date()
				)
		context['valid_cert_count'] = context['valid_certifications'].count()
		
		context['expiring_certifications'] = certifications.filter(
				is_valid=True,
				expiry_date__gte=timezone.now().date(),
				expiry_date__lte=timezone.now().date() + timedelta(days=30)
				)
		context['expiring_cert_count'] = context['expiring_certifications'].count()
		
		context['expired_certifications'] = certifications.filter(
				Q(is_valid=False) | Q(expiry_date__lt=timezone.now().date())
				)
		context['expired_cert_count'] = context['expired_certifications'].count()
		
		# Timesheet Summary
		timesheet_data = employee.timesheets.aggregate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				total_days=Count('date', distinct=True),
				avg_hours_per_day=Avg('hours_worked'),
				total_entries=Count('id')
				)
		context['timesheet_summary'] = timesheet_data
		
		# Monthly hours
		month_start = timezone.now().date().replace(day=1)
		monthly_data = employee.timesheets.filter(date__gte=month_start).aggregate(
				month_hours=Sum('hours_worked'),
				month_overtime=Sum('overtime_hours'),
				month_days=Count('date', distinct=True)
				)
		context['monthly_data'] = monthly_data
		
		# Weekly hours
		week_start = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
		weekly_data = employee.timesheets.filter(date__gte=week_start).aggregate(
				week_hours=Sum('hours_worked'),
				week_overtime=Sum('overtime_hours'),
				week_days=Count('date', distinct=True)
				)
		context['weekly_data'] = weekly_data
		
		# Recent Timesheets
		context['recent_timesheets'] = employee.timesheets.select_related(
				'work_package__project', 'work_package__area', 'approved_by'
				).order_by('-date', '-created_at')[:20]
		
		# Work Package History
		context['work_package_history'] = employee.timesheets.values(
				'work_package__code',
				'work_package__name',
				'work_package_id',
				'work_package__project__name'
				).annotate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				days_worked=Count('date', distinct=True),
				first_date=Min('date'),
				last_date=Max('date')
				).order_by('-last_date')
		
		# Daily hours for last 30 days (for chart)
		daily_hours = []
		for i in range(29, -1, -1):
			day = timezone.now().date() - timedelta(days=i)
			day_data = employee.timesheets.filter(date=day).aggregate(
					hours=Sum('hours_worked'),
					overtime=Sum('overtime_hours')
					)
			daily_hours.append({
					'date': day,
					'day_name': day.strftime('%a'),
					'day_num': day.strftime('%d'),
					'hours': float(day_data['hours'] or 0),
					'overtime': float(day_data['overtime'] or 0),
					'has_entry': employee.timesheets.filter(date=day).exists()
					})
		context['daily_hours'] = daily_hours
		
		# Active work package (most recent)
		context['current_work_package'] = employee.timesheets.select_related(
				'work_package__project'
				).order_by('-date').first()
		
		# Total career statistics
		first_timesheet = employee.timesheets.order_by('date').first()
		if first_timesheet:
			context['career_start'] = first_timesheet.date
			context['career_days'] = (timezone.now().date() - first_timesheet.date).days
		
		# Pending timesheets
		context['pending_timesheets'] = employee.timesheets.filter(
				is_approved=False
				).order_by('-date')[:10]
		context['pending_count'] = employee.timesheets.filter(is_approved=False).count()
		
		# Approved timesheets
		context['approved_count'] = employee.timesheets.filter(is_approved=True).count()
		
		# Current date
		context['today'] = timezone.now().date()
		
		return context


class EmployeeDetailView(LoginRequiredMixin, generic.DetailView):
	"""View employee details with certifications, timesheets, and work history."""
	model = Employee
	template_name = 'resources/employee_detail.html'
	context_object_name = 'employee'
	
	def get_queryset(self):
		return Employee.objects.select_related('user').prefetch_related(
				'certifications',
				'timesheets__work_package__project',
				'timesheets__work_package__area'
				)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		employee = self.get_object()
		
		# Certifications
		certifications = employee.certifications.all().order_by('-expiry_date')
		context['certifications'] = certifications
		context['valid_certifications'] = certifications.filter(
				is_valid=True,
				expiry_date__gte=timezone.now().date()
				)
		context['expired_certifications'] = certifications.filter(
				Q(is_valid=False) | Q(expiry_date__lt=timezone.now().date())
				)
		context['expiring_soon_certifications'] = certifications.filter(
				is_valid=True,
				expiry_date__lte=timezone.now().date() + timedelta(days=30),
				expiry_date__gte=timezone.now().date()
				)
		
		# Timesheet summary
		timesheet_queryset = employee.timesheets.all()
		
		timesheet_stats = timesheet_queryset.aggregate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				total_days=Count('date', distinct=True),
				total_entries=Count('id')
				)
		
		context['timesheet_stats'] = timesheet_stats
		context['total_hours'] = timesheet_stats['total_hours'] or 0
		context['total_overtime'] = timesheet_stats['total_overtime'] or 0
		context['total_days_worked'] = timesheet_stats['total_days'] or 0
		context['total_entries'] = timesheet_stats['total_entries'] or 0
		
		# Recent timesheets (last 20)
		context['recent_timesheets'] = timesheet_queryset.select_related(
				'work_package__project', 'approved_by'
				).order_by('-date')[:20]
		
		# This week's hours
		today = timezone.now().date()
		week_start = today - timedelta(days=today.weekday())
		week_end = week_start + timedelta(days=6)
		
		week_timesheets = timesheet_queryset.filter(date__gte=week_start, date__lte=week_end)
		week_stats = week_timesheets.aggregate(
				hours=Sum('hours_worked'),
				overtime=Sum('overtime_hours')
				)
		context['week_hours'] = week_stats['hours'] or 0
		context['week_overtime'] = week_stats['overtime'] or 0
		
		# This month's hours
		month_start = today.replace(day=1)
		month_timesheets = timesheet_queryset.filter(date__gte=month_start)
		month_stats = month_timesheets.aggregate(
				hours=Sum('hours_worked'),
				overtime=Sum('overtime_hours')
				)
		context['month_hours'] = month_stats['hours'] or 0
		context['month_overtime'] = month_stats['overtime'] or 0
		
		# Work package history
		context['work_package_history'] = timesheet_queryset.values(
				'work_package__code',
				'work_package__name',
				'work_package_id',
				'work_package__project__name'
				).annotate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				days_worked=Count('date', distinct=True),
				first_date=Min('date'),
				last_date=Max('date')
				).order_by('-last_date')[:15]
		
		# Daily hours for the last 14 days (for chart)
		daily_hours = []
		for i in range(13, -1, -1):
			day = today - timedelta(days=i)
			day_data = timesheet_queryset.filter(date=day).aggregate(
					hours=Sum('hours_worked'),
					overtime=Sum('overtime_hours')
					)
			daily_hours.append({
					'date': day,
					'day_name': day.strftime('%a'),
					'day_number': day.strftime('%d'),
					'hours': float(day_data['hours'] or 0),
					'overtime': float(day_data['overtime'] or 0),
					'is_today': day == today,
					'is_weekend': day.weekday() >= 5
					})
		context['daily_hours'] = daily_hours
		
		# Weekly hours for the last 8 weeks
		weekly_hours = []
		for i in range(7, -1, -1):
			week_start_date = today - timedelta(days=today.weekday() + (i * 7))
			week_end_date = week_start_date + timedelta(days=6)
			week_data = timesheet_queryset.filter(
					date__gte=week_start_date,
					date__lte=week_end_date
					).aggregate(
					hours=Sum('hours_worked'),
					overtime=Sum('overtime_hours')
					)
			weekly_hours.append({
					'week_start': week_start_date,
					'week_end': week_end_date,
					'label': f"{week_start_date.strftime('%b %d')}",
					'hours': float(week_data['hours'] or 0),
					'overtime': float(week_data['overtime'] or 0)
					})
		context['weekly_hours'] = weekly_hours
		
		# Pending approval timesheets
		context['pending_timesheets'] = timesheet_queryset.filter(
				is_approved=False
				).select_related('work_package').order_by('-date')[:10]
		context['pending_count'] = timesheet_queryset.filter(is_approved=False).count()
		
		# Approved timesheets
		context['approved_timesheets'] = timesheet_queryset.filter(
				is_approved=True
				).count()
		
		# Average hours per day
		if context['total_days_worked'] > 0:
			context['avg_hours_per_day'] = round(
					context['total_hours'] / context['total_days_worked'], 1
					)
		else:
			context['avg_hours_per_day'] = 0
		
		# Current date
		context['today'] = today
		
		return context

class TimesheetListView(LoginRequiredMixin, generic.ListView):
	model = Timesheet
	template_name = 'resources/timesheet_list.html'
	context_object_name = 'timesheets'
	paginate_by = 50
	
	def get_queryset(self):
		queryset = Timesheet.objects.select_related(
				'employee',
				'work_package__project',
				'work_package__area',
				'approved_by'
				)
		
		# Apply filters
		form = TimesheetSearchForm(self.request.GET)
		if form.is_valid():
			data = form.cleaned_data
			
			if data.get('employee'):
				queryset = queryset.filter(employee=data['employee'])
			
			if data.get('work_package'):
				queryset = queryset.filter(work_package=data['work_package'])
			
			if data.get('project'):
				queryset = queryset.filter(work_package__project=data['project'])
			
			if data.get('company'):
				queryset = queryset.filter(employee__company__icontains=data['company'])
			
			if data.get('trade'):
				queryset = queryset.filter(employee__trade=data['trade'])
			
			if data.get('date_from'):
				queryset = queryset.filter(date__gte=data['date_from'])
			
			if data.get('date_to'):
				queryset = queryset.filter(date__lte=data['date_to'])
			
			if data.get('is_approved') in ['true', 'false']:
				queryset = queryset.filter(is_approved=data['is_approved'] == 'true')
			
			if data.get('search'):
				search = data['search']
				queryset = queryset.filter(
						Q(employee__first_name__icontains=search) |
						Q(employee__last_name__icontains=search) |
						Q(employee__employee_id__icontains=search) |
						Q(work_package__code__icontains=search) |
						Q(work_package__name__icontains=search)
						)
		
		# Apply sorting
		sort = self.request.GET.get('sort', '-date')
		allowed_sorts = [
				'date', '-date',
				'employee__last_name', '-employee__last_name',
				'employee__first_name', '-employee__first_name',
				'hours_worked', '-hours_worked',
				'work_package__code', '-work_package__code',
				'is_approved', '-is_approved',
				]
		if sort in allowed_sorts:
			queryset = queryset.order_by(sort)
		
		return queryset
	
	def get_paginate_by(self, queryset):
		per_page = self.request.GET.get('per_page', '50')
		try:
			return min(int(per_page), 200)
		except ValueError:
			return 50
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Search form
		context['search_form'] = TimesheetSearchForm(self.request.GET)
		
		# View mode
		context['view_mode'] = self.request.GET.get('view', 'table')
		
		# Date range for filtering
		date_from = self.request.GET.get('date_from')
		date_to = self.request.GET.get('date_to')
		
		if not date_from:
			date_from = (timezone.now().date() - timedelta(days=30)).isoformat()
		if not date_to:
			date_to = timezone.now().date().isoformat()
		
		# Base queryset for statistics
		base_queryset = Timesheet.objects.all()
		
		# Apply same project filter for stats
		project_id = self.request.GET.get('project')
		if project_id:
			base_queryset = base_queryset.filter(work_package__project_id=project_id)
		
		# Statistics
		stats = base_queryset.aggregate(
				total_entries=Count('id'),
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				avg_hours_per_day=Avg('hours_worked'),
				total_employees=Count('employee', distinct=True),
				total_work_packages=Count('work_package', distinct=True)
				)
		
		context['total_entries'] = stats['total_entries'] or 0
		context['total_hours'] = stats['total_hours'] or 0
		context['total_overtime'] = stats['total_overtime'] or 0
		context['avg_hours_per_day'] = round(stats['avg_hours_per_day'] or 0, 1)
		context['total_employees'] = stats['total_employees'] or 0
		context['total_work_packages'] = stats['total_work_packages'] or 0
		
		# Pending approval count
		context['pending_approval'] = base_queryset.filter(is_approved=False).count()
		
		# Weekly summary
		today = timezone.now().date()
		week_start = today - timedelta(days=today.weekday())
		week_end = week_start + timedelta(days=6)
		
		weekly_data = base_queryset.filter(
				date__gte=week_start,
				date__lte=week_end
				).aggregate(
				week_hours=Sum('hours_worked'),
				week_overtime=Sum('overtime_hours'),
				week_employees=Count('employee', distinct=True)
				)
		
		context['week_hours'] = weekly_data['week_hours'] or 0
		context['week_overtime'] = weekly_data['week_overtime'] or 0
		context['week_employees'] = weekly_data['week_employees'] or 0
		
		# Top employees by hours
		context['top_employees'] = base_queryset.values(
				'employee__first_name',
				'employee__last_name',
				'employee__employee_id',
				'employee__company'
				).annotate(
				total_hours=Sum('hours_worked'),
				total_days=Count('date', distinct=True)
				).order_by('-total_hours')[:10]
		
		# Hours by work package
		context['hours_by_work_package'] = base_queryset.values(
				'work_package__code',
				'work_package__name',
				'work_package_id'
				).annotate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				employee_count=Count('employee', distinct=True)
				).order_by('-total_hours')[:10]
		
		# Daily hours for the last 7 days (for chart)
		daily_hours = []
		for i in range(6, -1, -1):
			day = today - timedelta(days=i)
			day_data = base_queryset.filter(date=day).aggregate(
					hours=Sum('hours_worked'),
					entries=Count('id')
					)
			daily_hours.append({
					'date': day,
					'day_name': day.strftime('%a'),
					'hours': float(day_data['hours'] or 0),
					'entries': day_data['entries'] or 0
					})
		context['daily_hours'] = daily_hours
		
		# Employees for filter dropdown
		context['employees'] = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
		
		# Work packages for filter dropdown
		context['work_packages'] = WorkPackage.objects.filter(
				status__in=['IPRO', 'MOB', 'NSTA']
				).select_related('project').order_by('code')
		
		# Current date
		context['today'] = today
		
		return context


class TimesheetCreateView(LoginRequiredMixin, generic.CreateView):
	"""Create a new timesheet entry."""
	model = Timesheet
	form_class = TimesheetForm
	template_name = 'resources/timesheet_form.html'
	success_message = "Timesheet entry was created successfully."
	
	def get_success_url(self):
		if self.request.POST.get('save_add_another'):
			return reverse('resources:timesheet_create')
		return reverse('resources:timesheet_list')
	
	def get_initial(self):
		initial = super().get_initial()
		
		# Pre-fill employee
		employee_id = self.kwargs.get('employee_id') or self.request.GET.get('employee')
		if employee_id:
			employee = get_object_or_404(Employee, pk=employee_id)
			initial['employee'] = employee
		
		# Pre-fill work package
		work_package_id = self.request.GET.get('work_package')
		if work_package_id:
			work_package = get_object_or_404(WorkPackage, pk=work_package_id)
			initial['work_package'] = work_package
		
		# Set today's date
		initial['date'] = timezone.now().date()
		
		# Default hours
		initial['hours_worked'] = 8.0
		initial['overtime_hours'] = 0.0
		
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = True
		context['page_title'] = 'Add Timesheet Entry'
		
		# Pre-selected employee info
		employee_id = self.kwargs.get('employee_id') or self.request.GET.get('employee')
		if employee_id:
			context['selected_employee'] = get_object_or_404(Employee, pk=employee_id)
		
		# Pre-selected work package info
		work_package_id = self.request.GET.get('work_package')
		if work_package_id:
			context['selected_work_package'] = get_object_or_404(WorkPackage, pk=work_package_id)
		
		# Active employees for quick selection
		context['active_employees'] = Employee.objects.filter(
				is_active=True
				).order_by('company', 'last_name', 'first_name')
		
		# Active work packages for quick selection
		context['active_work_packages'] = WorkPackage.objects.filter(
				status__in=['IPRO', 'MOB', 'NSTA']
				).select_related('project', 'area').order_by('code')
		
		# Recent timesheets for this employee
		if employee_id:
			context['recent_timesheets'] = Timesheet.objects.filter(
					employee_id=employee_id
					).select_related('work_package').order_by('-date')[:10]
		
		# Today's existing entries
		today = timezone.now().date()
		if employee_id:
			context['today_entry'] = Timesheet.objects.filter(
					employee_id=employee_id,
					date=today
					).first()
		
		# Employee companies for filtering
		context['companies'] = Employee.objects.filter(
				is_active=True
				).values_list('company', flat=True).distinct().order_by('company')
		
		return context
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		employee_id = self.kwargs.get('employee_id') or self.request.GET.get('employee')
		if employee_id:
			kwargs['employee_id'] = int(employee_id)
		return kwargs
	
	def form_valid(self, form):
		# Check for duplicate entry
		employee = form.cleaned_data['employee']
		work_package = form.cleaned_data['work_package']
		date = form.cleaned_data['date']
		
		existing = Timesheet.objects.filter(
				employee=employee,
				work_package=work_package,
				date=date
				).first()
		
		if existing:
			messages.warning(
					self.request,
					f'A timesheet entry for {employee.full_name} on {date} already exists. '
					f'Please update the existing entry instead.'
					)
			return redirect('resources:timesheet_update', pk=existing.pk)
		
		messages.success(
				self.request,
				f'Timesheet entry for {employee.full_name} on {date} was created successfully.'
				)
		return super().form_valid(form)
	
	def form_invalid(self, form):
		messages.error(self.request, 'Please correct the errors below.')
		return super().form_invalid(form)


class TimesheetUpdateView(LoginRequiredMixin, generic.UpdateView):
	"""Update an existing timesheet entry."""
	model = Timesheet
	form_class = TimesheetForm
	template_name = 'resources/timesheet_form.html'
	success_message = "Timesheet entry was updated successfully."
	
	def get_success_url(self):
		return reverse('resources:timesheet_list')
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = False
		context['page_title'] = f'Edit Timesheet - {self.object.date}'
		context['selected_employee'] = self.object.employee
		context['selected_work_package'] = self.object.work_package
		context['recent_timesheets'] = Timesheet.objects.filter(
				employee=self.object.employee
				).select_related('work_package').order_by('-date')[:10]
		return context
	
	def form_valid(self, form):
		messages.success(
				self.request,
				f'Timesheet entry for {form.cleaned_data["employee"].full_name} was updated successfully.'
				)
		return super().form_valid(form)


def timesheet_bulk_create_view(request):
	"""Bulk create timesheet entries for multiple employees."""
	
	if request.method == 'POST':
		form = TimesheetBulkForm(request.POST)
		
		if form.is_valid():
			data = form.cleaned_data
			work_package = data['work_package']
			date = data['date']
			employees = data['employees']
			default_hours = data['default_hours']
			overtime_hours = data.get('overtime_hours', 0)
			notes = data.get('notes', '')
			
			created_count = 0
			skipped_count = 0
			error_count = 0
			
			with transaction.atomic():
				for employee in employees:
					# Check for duplicate
					if Timesheet.objects.filter(
							employee=employee,
							work_package=work_package,
							date=date
							).exists():
						skipped_count += 1
						continue
					
					try:
						Timesheet.objects.create(
								employee=employee,
								work_package=work_package,
								date=date,
								hours_worked=default_hours,
								overtime_hours=overtime_hours,
								notes=notes
								)
						created_count += 1
					except Exception:
						error_count += 1
			
			if created_count > 0:
				messages.success(
						request,
						f'Successfully created {created_count} timesheet entries.'
						)
			if skipped_count > 0:
				messages.warning(
						request,
						f'{skipped_count} entries were skipped (already exist).'
						)
			if error_count > 0:
				messages.error(
						request,
						f'{error_count} entries failed to create.'
						)
			
			return redirect('resources:timesheet_list')
	else:
		form = TimesheetBulkForm()
	
	context = {
			'form': form,
			'page_title': 'Bulk Add Timesheets',
			'active_employees': Employee.objects.filter(is_active=True).order_by('company', 'last_name'),
			'active_work_packages': WorkPackage.objects.filter(
					status__in=['IPRO', 'MOB', 'NSTA']
					).select_related('project').order_by('code'),
			'companies': Employee.objects.filter(is_active=True).values_list(
					'company', flat=True
					).distinct().order_by('company'),
			}
	
	return render(request, 'resources/timesheet_bulk_form.html', context)


def timesheet_approve_view(request, pk):
	"""Approve a timesheet entry."""
	timesheet = get_object_or_404(Timesheet, pk=pk)
	
	if request.method == 'POST':
		timesheet.is_approved = True
		timesheet.approved_by = request.user
		timesheet.save()
		
		messages.success(
				request,
				f'Timesheet for {timesheet.employee.full_name} on {timesheet.date} was approved.'
				)
	
	# Redirect back to the referring page
	referer = request.META.get('HTTP_REFERER')
	if referer:
		return redirect(referer)
	return redirect('resources:timesheet_list')
