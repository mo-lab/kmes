from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.utils import timezone
from django.views.generic import CreateView, ListView

from .models import WorkPackage, WorkPackageItem, DailyProgressReport, DailyProcessReportEmployees
from core.models import Project, Area, System, EquipmentTag
from .forms import WorkPackageForm, WorkPackageItemForm, WorkPackageSearchForm, DailyProgressReportForm, WorkPackageProgressUpdateForm, \
	WorkPackageItemBulkForm, DailyProccessReportEmployeeForm, DailyProgressReportForm2
from django.db.models import Q, Count, Case, When, Value, CharField, Sum, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta, date

from .models import DailyProgressReport, WorkPackage
from .forms import DailyReportSearchForm
from resources.models import Employee,Timesheet


class WorkPackageCreateView(LoginRequiredMixin, generic.CreateView):
	"""Create a new work package with optional equipment tags."""
	model = WorkPackage
	form_class = WorkPackageForm
	template_name = 'construction/work_package_form.html'
	success_message = "Work Package '%(code)s' was created successfully."
	
	def get_success_url(self):
		return HttpResponse('success')
	
	def get_initial(self):
		initial = super().get_initial()
		
		# Pre-fill from URL parameters
		project_id = self.kwargs.get('project_id') or self.request.GET.get('project')
		if project_id:
			initial['project'] = get_object_or_404(Project, pk=project_id)
		
		area_id = self.kwargs.get('area_id') or self.request.GET.get('area')
		if area_id:
			initial['area'] = get_object_or_404(Area, pk=area_id)
		
		system_id = self.request.GET.get('system')
		if system_id:
			initial['system'] = get_object_or_404(System, pk=system_id)
		
		# Set default dates
		initial['planned_start'] = timezone.now().date()
		
		# Auto-generate work package code
		if project_id:
			initial['code'] = self.generate_work_package_code(project_id)
		
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = True
		context['page_title'] = 'Create New Work Package'
		
		# Get project for context
		project_id = self.kwargs.get('project_id') or self.request.GET.get('project')
		if project_id:
			context['project'] = get_object_or_404(Project, pk=project_id)
			
			# Available equipment tags for this project
			context['available_tags'] = EquipmentTag.objects.filter(
					project_id=project_id
					).select_related('area').order_by('tag_number')
		
		# Recent work packages for reference
		context['recent_work_packages'] = WorkPackage.objects.select_related(
				'project', 'area', 'supervisor'
				).order_by('-created_at')[:5]
		
		return context
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		project_id = self.kwargs.get('project_id') or self.request.GET.get('project')
		if project_id:
			kwargs['project_id'] = int(project_id)
		return kwargs
	
	@transaction.atomic
	def form_valid(self, form):
		# Save the work package
		self.object = form.save(commit=False)
		
		# Set supervisor if not specified
		if not self.object.supervisor:
			self.object.supervisor = self.request.user
		
		self.object.save()
		
		# Handle equipment tags
		tag_ids = self.request.POST.getlist('equipment_tags')
		if tag_ids:
			self.add_equipment_tags(tag_ids)
		
		# Handle bulk tag selection by area
		area_id = self.request.POST.get('bulk_add_area')
		if area_id and self.request.POST.get('add_all_area_tags'):
			self.add_all_area_tags(area_id)
		
		# Handle bulk tag selection by system
		system_id = self.request.POST.get('bulk_add_system')
		if system_id and self.request.POST.get('add_all_system_tags'):
			self.add_all_system_tags(system_id)
		
		# Handle tag search and add
		tag_search = self.request.POST.get('tag_search')
		if tag_search and self.request.POST.get('add_search_results'):
			self.add_search_results_tags(tag_search)
		
		messages.success(
				self.request,
				self.success_message % {'code': self.object.code}
				)
		
		# Show count of added tags
		tag_count = self.object.items.count()
		if tag_count > 0:
			messages.info(
					self.request,
					f'{tag_count} equipment tag(s) added to this work package.'
					)
		
		return HttpResponse('success') #redirect(self.get_success_url())
	
	def form_invalid(self, form):
		messages.error(self.request, 'Please correct the errors below.')
		return super().form_invalid(form)
	
	def add_equipment_tags(self, tag_ids):
		"""Add selected equipment tags to the work package."""
		sequence = self.object.items.count() + 1
		
		for tag_id in tag_ids:
			try:
				tag = EquipmentTag.objects.get(pk=tag_id, project_id=self.object.project_id)
				
				# Check if tag is already in this work package
				if not WorkPackageItem.objects.filter(
						work_package=self.object,
						equipment_tag=tag
						).exists():
					WorkPackageItem.objects.create(
							work_package=self.object,
							equipment_tag=tag,
							sequence_number=sequence
							)
					sequence += 1
			except EquipmentTag.DoesNotExist:
				continue
	
	def add_all_area_tags(self, area_id):
		"""Add all tags from a specific area."""
		try:
			area = Area.objects.get(pk=area_id, project_id=self.object.project_id)
			tags = EquipmentTag.objects.filter(
					project_id=self.object.project_id,
					area=area
					).exclude(
					work_package_items__work_package=self.object
					)
			
			sequence = self.object.items.count() + 1
			for tag in tags:
				WorkPackageItem.objects.create(
						work_package=self.object,
						equipment_tag=tag,
						sequence_number=sequence
						)
				sequence += 1
		except Area.DoesNotExist:
			pass
	
	def add_all_system_tags(self, system_id):
		"""Add all tags from a specific system."""
		try:
			system = System.objects.get(pk=system_id, project_id=self.object.project_id)
			tags = EquipmentTag.objects.filter(
					project_id=self.object.project_id,
					system=system
					).exclude(
					work_package_items__work_package=self.object
					)
			
			sequence = self.object.items.count() + 1
			for tag in tags:
				WorkPackageItem.objects.create(
						work_package=self.object,
						equipment_tag=tag,
						sequence_number=sequence
						)
				sequence += 1
		except System.DoesNotExist:
			pass
	
	def add_search_results_tags(self, search_term):
		"""Add tags matching search criteria."""
		tags = EquipmentTag.objects.filter(
				project_id=self.object.project_id
				).filter(
				Q(tag_number__icontains=search_term) |
				Q(description__icontains=search_term)
				).exclude(
				work_package_items__work_package=self.object
				)
		
		sequence = self.object.items.count() + 1
		for tag in tags[:50]:  # Limit to 50 tags
			WorkPackageItem.objects.create(
					work_package=self.object,
					equipment_tag=tag,
					sequence_number=sequence
					)
			sequence += 1
	
	def generate_work_package_code(self, project_id):
		"""Generate a unique work package code."""
		try:
			project = Project.objects.get(pk=project_id)
			project_prefix = project.code[:4].upper() if project.code else 'WP'
		except Project.DoesNotExist:
			project_prefix = 'WP'
		
		# Count existing work packages for this project
		count = WorkPackage.objects.filter(project_id=project_id).count() + 1
		
		# Get current year and month
		now = timezone.now()
		year_month = now.strftime('%y%m')
		
		return f"{project_prefix}-{year_month}-{count:03d}"


class WorkPackageUpdateView(LoginRequiredMixin, generic.UpdateView):
	"""Update an existing work package."""
	model = WorkPackage
	form_class = WorkPackageForm
	template_name = 'construction/work_package_form.html'
	success_message = "Work Package '%(code)s' was updated successfully."
	
	def get_success_url(self):
		return HttpResponse('success')
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = False
		context['page_title'] = f'Edit Work Package: {self.object.code}'
		context['project'] = self.object.project
		
		# Get existing items
		context['work_package_items'] = self.object.items.select_related(
				'equipment_tag__area'
				).order_by('sequence_number')
		
		# Available tags not yet in this work package
		context['available_tags'] = EquipmentTag.objects.filter(
				project=self.object.project
				).exclude(
				work_package_items__work_package=self.object
				).select_related('area').order_by('tag_number')
		
		return context
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		if self.object.project_id:
			kwargs['project_id'] = self.object.project_id
		return kwargs
	
	@transaction.atomic
	def form_valid(self, form):
		self.object = form.save()
		
		# Handle adding new tags
		tag_ids = self.request.POST.getlist('equipment_tags')
		if tag_ids:
			sequence = self.object.items.count() + 1
			for tag_id in tag_ids:
				try:
					tag = EquipmentTag.objects.get(
							pk=tag_id,
							project_id=self.object.project_id
							)
					if not WorkPackageItem.objects.filter(
							work_package=self.object,
							equipment_tag=tag
							).exists():
						WorkPackageItem.objects.create(
								work_package=self.object,
								equipment_tag=tag,
								sequence_number=sequence
								)
						sequence += 1
				except EquipmentTag.DoesNotExist:
					continue
		
		# Handle removing tags
		remove_tag_ids = self.request.POST.getlist('remove_tags')
		if remove_tag_ids:
			WorkPackageItem.objects.filter(
					work_package=self.object,
					equipment_tag_id__in=remove_tag_ids
					).delete()
		
		# Handle reordering
		item_order = self.request.POST.getlist('item_order')
		if item_order:
			for index, item_id in enumerate(item_order, start=1):
				WorkPackageItem.objects.filter(
						pk=item_id,
						work_package=self.object
						).update(sequence_number=index)
		
		messages.success(
				self.request,
				self.success_message % {'code': self.object.code}
				)
		
		return redirect(self.get_success_url())




class WorkPackageListView( generic.ListView):
	model = WorkPackage
	template_name = 'construction/work_package_list.html'
	context_object_name = 'work_packages'
	paginate_by = 20
	
	def get_queryset(self):
		queryset = WorkPackage.objects.select_related(
				'project', 'area', 'system', 'supervisor'
				).prefetch_related(
				'items__equipment_tag',
				'daily_reports',
				'timesheets',
				'tool_assignments'
				).annotate(
				item_count=Count('items', distinct=True),
				report_count=Count('daily_reports', distinct=True),
				timesheet_count=Count('timesheets', distinct=True),
				completed_items=Count(
						Case(
								When(items__is_complete=True, then=1),
								output_field=CharField(),
								),
						distinct=True
						)
				)
		
		# Apply filters
		form = WorkPackageSearchForm(self.request.GET)
		if form.is_valid():
			data = form.cleaned_data
			
			if data.get('project'):
				queryset = queryset.filter(project=data['project'])
			
			if data.get('area'):
				queryset = queryset.filter(area=data['area'])
			
			if data.get('status'):
				queryset = queryset.filter(status=data['status'])
			
			if data.get('priority'):
				queryset = queryset.filter(priority=data['priority'])
			
			if data.get('contractor'):
				queryset = queryset.filter(contractor__icontains=data['contractor'])
			
			if data.get('search'):
				search = data['search']
				queryset = queryset.filter(
						Q(code__icontains=search) |
						Q(name__icontains=search) |
						Q(description__icontains=search) |
						Q(contractor__icontains=search)
						)
			
			if data.get('date_from'):
				queryset = queryset.filter(planned_start__gte=data['date_from'])
			
			if data.get('date_to'):
				queryset = queryset.filter(planned_finish__lte=data['date_to'])
			
			if data.get('overdue_only'):
				queryset = queryset.filter(
						status__in=['IPRO', 'NSTA', 'MOB'],
						planned_finish__lt=timezone.now().date()
						)
		
		# Apply sorting
		sort = self.request.GET.get('sort', 'code')
		allowed_sorts = [
				'code', '-code',
				'name', '-name',
				'planned_start', '-planned_start',
				'planned_finish', '-planned_finish',
				'status', '-status',
				'priority', '-priority',
				'percent_complete', '-percent_complete',
				'created_at', '-created_at',
				]
		if sort in allowed_sorts:
			queryset = queryset.order_by(sort)
		
		return queryset
	
	def get_paginate_by(self, queryset):
		per_page = self.request.GET.get('per_page', '20')
		try:
			return min(int(per_page), 100)
		except ValueError:
			return 20
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Search form
		context['search_form'] = WorkPackageSearchForm(self.request.GET)
		
		# View mode
		context['view_mode'] = self.request.GET.get('view', 'table')
		
		# Statistics
		base_queryset = WorkPackage.objects.all()
		project_id = self.request.GET.get('project')
		if project_id:
			base_queryset = base_queryset.filter(project_id=project_id)
		
		context['total_work_packages'] = base_queryset.count()
		context['active_work_packages'] = base_queryset.filter(status='IPRO').count()
		context['completed_work_packages'] = base_queryset.filter(status='COMP').count()
		context['not_started_work_packages'] = base_queryset.filter(status='NSTA').count()
		context['on_hold_work_packages'] = base_queryset.filter(status='HOLD').count()
		
		# Overdue work packages
		context['overdue_count'] = base_queryset.filter(
				status__in=['IPRO', 'NSTA', 'MOB'],
				planned_finish__lt=timezone.now().date()
				).count()
		
		# Total equipment tags across all work packages
		context['total_equipment_tags'] = WorkPackageItem.objects.filter(
				work_package__in=base_queryset
				).count()
		
		# Progress statistics
		context['avg_progress'] = base_queryset.aggregate(
				avg=Avg('percent_complete')
				)['avg'] or 0
		
		# Projects for filter
		context['projects'] = Project.objects.all()
		
		# Areas for filter
		if project_id:
			context['areas'] = Area.objects.filter(project_id=project_id)
		else:
			context['areas'] = Area.objects.all()
		
		# Recent activity
		context['recent_reports'] = DailyProgressReport.objects.filter(
				work_package__in=base_queryset
				).select_related('work_package', 'reported_by').order_by('-report_date')[:5]
		
		# Current time for calculations
		context['now'] = timezone.now()
		
		return context


class DailyProgressReportCreateView(LoginRequiredMixin, generic.CreateView):
	"""Create a daily progress report for a work package."""
	model = DailyProgressReport
	form_class = DailyProgressReportForm
	template_name = 'construction/daily_report_form.html'
	success_message = "Daily progress report was created successfully."
	
	def get_success_url(self):
		return HttpResponse('success')#reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
	
	def get_initial(self):
		initial = super().get_initial()
		
		# Pre-fill work package
		work_package_id = self.kwargs.get('work_package_id') or self.request.GET.get('work_package')
		if work_package_id:
			work_package = get_object_or_404(WorkPackage, pk=work_package_id)
			initial['work_package'] = work_package
		
		# Set today's date
		initial['report_date'] = timezone.now().date()
		
		# Try to get yesterday's report for continuity
		if work_package_id:
			yesterday = timezone.now().date() - timedelta(days=1)
			yesterday_report = DailyProgressReport.objects.filter(
					work_package_id=work_package_id,
					report_date=yesterday
					).first()
			
			if yesterday_report:
				initial['weather_conditions'] = yesterday_report.weather_conditions
				initial['temperature_celsius'] = yesterday_report.temperature_celsius
		
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = True
		context['page_title'] = 'Create Daily Progress Report'
		
		# Get work package info
		work_package_id = self.kwargs.get('work_package_id') or self.request.GET.get('work_package')
		if work_package_id:
			work_package = get_object_or_404(WorkPackage, pk=work_package_id)
			context['work_package'] = work_package
			
			# Get equipment tags for this work package
			context['work_package_items'] = work_package.items.select_related(
					'equipment_tag'
					).order_by('sequence_number')
			
			# Get previous reports
			context['previous_reports'] = DailyProgressReport.objects.filter(
					work_package=work_package
					).select_related('reported_by').order_by('-report_date')[:5]
			
			# Get today's manpower if already reported
			today = timezone.now().date()
			context['today_report'] = DailyProgressReport.objects.filter(
					work_package=work_package,
					report_date=today
					).first()
		
		# Active work packages for selection
		context['active_work_packages'] = WorkPackage.objects.filter(
				status__in=['IPRO', 'MOB']
				).select_related('project', 'area').order_by('code')
		
		# Weather options
		context['weather_options'] = [
				'Sunny', 'Partly Cloudy', 'Cloudy', 'Overcast',
				'Light Rain', 'Rain', 'Heavy Rain', 'Thunderstorm',
				'Snow', 'Windy', 'Foggy', 'Dust Storm'
				]
		
		return context
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		work_package_id = self.kwargs.get('work_package_id') or self.request.GET.get('work_package')
		if work_package_id:
			kwargs['work_package_id'] = int(work_package_id)
		return kwargs
	
	def form_valid(self, form):
		# Set the reporter
		form.instance.reported_by = self.request.user
		
		# Check if report already exists for today
		existing_report = DailyProgressReport.objects.filter(
				work_package=form.cleaned_data['work_package'],
				report_date=form.cleaned_data['report_date']
				).first()
		
		if existing_report:
			messages.warning(
					self.request,
					f'A report for {form.cleaned_data["report_date"]} already exists. '
					f'Please update the existing report instead.'
					)
			return redirect(
					'construction:daily_report_update',
					pk=existing_report.pk
					)
		
		# Save the report
		response = super().form_valid(form)
		
		# Update work package progress based on report
		self.update_work_package_progress(form)
		
		messages.success(self.request, self.success_message)
		return response
	
	def form_invalid(self, form):
		messages.error(self.request, 'Please correct the errors below.')
		return super().form_invalid(form)
	
	def update_work_package_progress(self, form):
		"""Update work package progress based on the daily report."""
		work_package = form.cleaned_data['work_package']
		
		# Auto-update status if needed
		if work_package.status == 'NSTA':
			work_package.status = 'IPRO'
			work_package.actual_start = work_package.actual_start or form.cleaned_data['report_date']
		
		# Calculate progress based on completed items
		total_items = work_package.items.count()
		if total_items > 0:
			completed_items = work_package.items.filter(is_complete=True).count()
			progress = int((completed_items / total_items) * 100)
			work_package.percent_complete = progress
			
			# Auto-complete if all items done
			if progress >= 100:
				work_package.status = 'COMP'
				work_package.actual_finish = work_package.actual_finish or form.cleaned_data['report_date']
		
		work_package.save()


class DailyProgressReportUpdateView(LoginRequiredMixin, generic.UpdateView):
	"""Update an existing daily progress report."""
	model = DailyProgressReport
	form_class = DailyProgressReportForm
	template_name = 'construction/daily_report_form.html'
	success_message = "Daily progress report was updated successfully."
	
	def get_success_url(self):
		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = False
		context['page_title'] = f'Edit Daily Report - {self.object.report_date}'
		context['work_package'] = self.object.work_package
		context['work_package_items'] = self.object.work_package.items.select_related(
				'equipment_tag'
				).order_by('sequence_number')
		context['previous_reports'] = DailyProgressReport.objects.filter(
				work_package=self.object.work_package
				).select_related('reported_by').order_by('-report_date')[:5]
		context['weather_options'] = [
				'Sunny', 'Partly Cloudy', 'Cloudy', 'Overcast',
				'Light Rain', 'Rain', 'Heavy Rain', 'Thunderstorm',
				'Snow', 'Windy', 'Foggy', 'Dust Storm'
				]
		return context
	
	def form_valid(self, form):
		form.instance.reported_by = self.request.user
		messages.success(self.request, self.success_message)
		return super().form_valid(form)


class DailyProgressReportListView(LoginRequiredMixin, generic.ListView):
	"""List all daily progress reports."""
	model = DailyProgressReport
	template_name = 'construction/daily_report_list.html'
	context_object_name = 'reports'
	paginate_by = 25
	
	def get_queryset(self):
		queryset = DailyProgressReport.objects.select_related(
				'work_package__project', 'work_package__area', 'reported_by'
				)
		
		# Filters
		work_package_id = self.request.GET.get('work_package')
		if work_package_id:
			queryset = queryset.filter(work_package_id=work_package_id)
		
		project_id = self.request.GET.get('project')
		if project_id:
			queryset = queryset.filter(work_package__project_id=project_id)
		
		date_from = self.request.GET.get('date_from')
		if date_from:
			queryset = queryset.filter(report_date__gte=date_from)
		
		date_to = self.request.GET.get('date_to')
		if date_to:
			queryset = queryset.filter(report_date__lte=date_to)
		
		return queryset.order_by('-report_date', '-created_at')
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['work_packages'] = WorkPackage.objects.filter(
				status__in=['IPRO', 'MOB']
				).select_related('project')
		context['projects'] = Project.objects.all()
		return context

class WorkPackageDetailView(LoginRequiredMixin, generic.DetailView):
	model = WorkPackage
	template_name = 'construction/work_package_detail.html'
	context_object_name = 'work_package'
	
	def get_queryset(self):
		return WorkPackage.objects.select_related(
				'project', 'area', 'system', 'supervisor'
				).prefetch_related(
				'items__equipment_tag__area',
				'daily_reports__reported_by',
				'timesheets__employee',
				'tool_assignments__tool_plant'
				)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		wp = self.get_object()
		
		# Equipment tags in this work package
		context['work_package_items'] = wp.items.select_related(
				'equipment_tag__area'
				).order_by('sequence_number')
		
		context['total_items'] = wp.items.count()
		context['completed_items'] = wp.items.filter(is_complete=True).count()
		context['pending_items'] = wp.items.filter(is_complete=False).count()
		
		# Calculate item progress
		if context['total_items'] > 0:
			context['item_progress'] = int((context['completed_items'] / context['total_items']) * 100)
		else:
			context['item_progress'] = 0
		
		# Daily Progress Reports
		context['daily_reports'] = wp.daily_reports.select_related(
				'reported_by'
				).order_by('-report_date')
		
		context['total_reports'] = wp.daily_reports.count()
		
		# Report statistics
		report_stats = wp.daily_reports.aggregate(
				total_manpower=Sum('manpower_count'),
				total_hours=Sum('hours_worked'),
				avg_manpower=Avg('manpower_count'),
				avg_hours=Avg('hours_worked')
				)
		context['report_stats'] = report_stats
		
		# Recent reports (last 7 days)
		seven_days_ago = timezone.now().date() - timedelta(days=7)
		context['recent_reports'] = wp.daily_reports.filter(
				report_date__gte=seven_days_ago
				).order_by('-report_date')
		
		# Reports with issues
		context['reports_with_issues'] = wp.daily_reports.filter(
				issues_encountered__isnull=False
				).exclude(issues_encountered='').count()
		
		# Timesheets
		context['timesheets'] = wp.timesheets.select_related(
				'employee'
				).order_by('-date')[:20]
		context['total_timesheets'] = wp.timesheets.count()
		
		# Total hours from timesheets
		timesheet_totals = wp.timesheets.aggregate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours')
				)
		context['timesheet_total_hours'] = timesheet_totals['total_hours'] or 0
		context['timesheet_total_overtime'] = timesheet_totals['total_overtime'] or 0
		
		# Tool assignments
		context['tool_assignments'] = wp.tool_assignments.select_related(
				'tool_plant'
				).order_by('-assignment_start')
		
		# Progress update form
		context['progress_form'] = WorkPackageProgressUpdateForm(instance=wp)
		
		# Schedule information
		context['is_overdue'] = (
				wp.planned_finish < timezone.now().date()
				and wp.status not in ['COMP', 'HOLD']
		)
		
		if wp.planned_start and wp.planned_finish:
			total_days = (wp.planned_finish - wp.planned_start).days
			if total_days > 0:
				if wp.actual_start:
					elapsed_days = (timezone.now().date() - wp.actual_start).days
				else:
					elapsed_days = (timezone.now().date() - wp.planned_start).days
				context['schedule_progress'] = min(int((elapsed_days / total_days) * 100), 100)
			else:
				context['schedule_progress'] = 0
		else:
			context['schedule_progress'] = 0
		
		# Weather summary from reports
		weather_summary = {}
		for report in context['recent_reports']:
			if report.weather_conditions:
				weather = report.weather_conditions.strip()
				weather_summary[weather] = weather_summary.get(weather, 0) + 1
		context['weather_summary'] = weather_summary
		
		# Recent activities
		context['activities'] = self.get_work_package_activities(wp)
		
		context['timesheets'] = wp.timesheets.select_related(
				'employee', 'approved_by'
				).order_by('-date', 'employee__last_name')

		context['total_timesheets'] = wp.timesheets.count()
		
		# Timesheet totals
		timesheet_totals = wp.timesheets.aggregate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours')
				)
		context['timesheet_total_hours'] = timesheet_totals['total_hours'] or 0
		context['timesheet_total_overtime'] = timesheet_totals['total_overtime'] or 0
		
		# Timesheets grouped by company
		context['timesheets_by_company'] = wp.timesheets.values(
				'employee__company'
				).annotate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				entry_count=Count('id'),
				worker_count=Count('employee', distinct=True)
				).order_by('-total_hours')
				
				# Timesheets grouped by trade
		context['timesheets_by_trade'] = wp.timesheets.values(
					'employee__trade'
					).annotate(
					count=Count('id'),
					total_hours=Sum('hours_worked')
					).order_by('-total_hours')
			
			# Timesheets by date (for chart)
		context['timesheets_by_date'] = wp.timesheets.values('date').annotate(
					total_hours=Sum('hours_worked'),
					total_overtime=Sum('overtime_hours'),
					worker_count=Count('employee', distinct=True)
					).order_by('-date')[:30]
			
		return context
	
	def get_work_package_activities(self, wp):
		"""Get recent activities for this work package."""
		activities = []
		
		# Add daily reports
		for report in wp.daily_reports.order_by('-created_at')[:5]:
			activities.append({
					'icon': 'journal-text',
					'description': f'Daily report submitted for {report.report_date}',
					'detail': f'{report.manpower_count} workers, {report.hours_worked or 0} hours',
					'date': report.created_at,
					'user': report.reported_by.get_full_name() if report.reported_by else 'System',
					'type': 'report'
					})
		
		# Add item completions
		completed_items = wp.items.filter(is_complete=True).order_by('-id')[:5]
		for item in completed_items:
			activities.append({
					'icon': 'check-circle',
					'description': f'Equipment tag {item.equipment_tag.tag_number} marked as complete',
					'detail': item.equipment_tag.description[:60],
					'date': item.installation_date or item.equipment_tag.updated_at,
					'user': 'System',
					'type': 'completion'
					})
		
		# Add tool assignments
		for assignment in wp.tool_assignments.order_by('-assignment_start')[:3]:
			activities.append({
					'icon': 'tools',
					'description': f'Tool assigned: {assignment.tool_plant.asset_number}',
					'detail': f'{assignment.tool_plant.get_tool_type_display()} - {assignment.tool_plant.make}',
					'date': assignment.assignment_start,
					'user': assignment.assigned_by.get_full_name() if assignment.assigned_by else 'System',
					'type': 'tool'
					})
		
		# Sort by date
		activities.sort(key=lambda x: x['date'], reverse=True)
		return activities[:15]


def work_package_progress_update_view(request, pk):
	"""Quick progress update for a work package."""
	work_package = get_object_or_404(WorkPackage, pk=pk)
	
	if request.method == 'POST':
		form = WorkPackageProgressUpdateForm(request.POST, instance=work_package)
		if form.is_valid():
			old_status = work_package.status
			wp = form.save(commit=False)
			
			# Auto-set actual dates based on status changes
			if old_status != wp.status:
				if wp.status == 'IPRO' and not wp.actual_start:
					wp.actual_start = timezone.now().date()
				elif wp.status == 'COMP' and not wp.actual_finish:
					wp.actual_finish = timezone.now().date()
			
			wp.save()
			messages.success(request, "Progress updated successfully.")
			return redirect('construction:work_package_detail', pk=work_package.pk)
		else:
			messages.error(request, "Please correct the errors below.")
	
	return redirect('construction:work_package_detail', pk=work_package.pk)


class WorkPackageItemCreateView(LoginRequiredMixin, generic.CreateView):
	"""Add equipment tags to a work package."""
	model = WorkPackageItem
	form_class = WorkPackageItemForm
	template_name = 'construction/work_package_item_form.html'
	success_message = "Equipment tag added to work package successfully."
	
	def get_success_url(self):
		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
	
	def get_initial(self):
		initial = super().get_initial()
		
		work_package_id = self.kwargs.get('work_package_id')
		if work_package_id:
			work_package = get_object_or_404(WorkPackage, pk=work_package_id)
			initial['work_package'] = work_package
			
			# Auto-increment sequence number
			last_sequence = work_package.items.order_by('-sequence_number').first()
			initial['sequence_number'] = (last_sequence.sequence_number + 1) if last_sequence else 1
		
		# Pre-select tag if provided
		tag_id = self.request.GET.get('tag')
		if tag_id:
			initial['equipment_tag'] = get_object_or_404(EquipmentTag, pk=tag_id)
		
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = True
		context['page_title'] = 'Add Equipment Tag to Work Package'
		
		work_package_id = self.kwargs.get('work_package_id')
		if work_package_id:
			work_package = get_object_or_404(WorkPackage, pk=work_package_id)
			context['work_package'] = work_package
			
			# Get already added tags
			context['existing_items'] = work_package.items.select_related(
					'equipment_tag__area'
					).order_by('sequence_number')
			
			# Get available tags (not yet in this work package)
			existing_tag_ids = work_package.items.values_list('equipment_tag_id', flat=True)
			context['available_tags'] = EquipmentTag.objects.filter(
					project=work_package.project
					).exclude(
					pk__in=existing_tag_ids
					).select_related('area').order_by('tag_number')
			
			# Group available tags by area
			context['tags_by_area'] = {}
			for tag in context['available_tags']:
				area_code = tag.area.code if tag.area else 'No Area'
				if area_code not in context['tags_by_area']:
					context['tags_by_area'][area_code] = []
				context['tags_by_area'][area_code].append(tag)
			
			# Areas for filtering
			context['areas'] = Area.objects.filter(project=work_package.project)
			
			# Systems for filtering
			context['systems'] = System.objects.filter(project=work_package.project)
		
		# Bulk form for adding multiple tags
		context['bulk_form'] = WorkPackageItemBulkForm(
				work_package_id=work_package_id if work_package_id else None
				)
		
		return context
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		work_package_id = self.kwargs.get('work_package_id')
		if work_package_id:
			kwargs['work_package_id'] = work_package_id
		return kwargs
	
	def form_valid(self, form):
		work_package = form.cleaned_data.get('work_package')
		equipment_tag = form.cleaned_data.get('equipment_tag')
		
		# Check if tag is already in the work package
		if WorkPackageItem.objects.filter(
				work_package=work_package,
				equipment_tag=equipment_tag
				).exists():
			messages.warning(
					self.request,
					f'Tag "{equipment_tag.tag_number}" is already in this work package.'
					)
			return redirect('construction:work_package_detail', pk=work_package.pk)
		
		# Check if tag belongs to the same project
		if equipment_tag.project_id != work_package.project_id:
			messages.error(
					self.request,
					'Equipment tag must belong to the same project as the work package.'
					)
			return self.form_invalid(form)
		
		messages.success(
				self.request,
				f'Tag "{equipment_tag.tag_number}" added successfully.'
				)
		return super().form_valid(form)
	
	def form_invalid(self, form):
		messages.error(self.request, 'Please correct the errors below.')
		return super().form_invalid(form)


def work_package_item_bulk_add_view(request, work_package_id):
	"""Bulk add multiple equipment tags to a work package."""
	work_package = get_object_or_404(WorkPackage, pk=work_package_id)
	
	if request.method == 'POST':
		form = WorkPackageItemBulkForm(request.POST, work_package_id=work_package_id)
		
		if form.is_valid():
			tag_ids = form.cleaned_data.get('equipment_tags')
			bulk_mode = form.cleaned_data.get('bulk_mode')
			
			added_count = 0
			skipped_count = 0
			
			with transaction.atomic():
				if bulk_mode == 'selected':
					# Add individually selected tags
					tags = EquipmentTag.objects.filter(
							pk__in=[int(tid) for tid in tag_ids.split(',') if tid]
							)
				elif bulk_mode == 'area':
					# Add all tags from selected area
					area_id = form.cleaned_data.get('area')
					if area_id:
						tags = EquipmentTag.objects.filter(
								project=work_package.project,
								area_id=area_id
								).exclude(
								work_package_items__work_package=work_package
								)
					else:
						tags = EquipmentTag.objects.none()
				elif bulk_mode == 'system':
					# Add all tags from selected system
					system_id = form.cleaned_data.get('system')
					if system_id:
						tags = EquipmentTag.objects.filter(
								project=work_package.project,
								system_id=system_id
								).exclude(
								work_package_items__work_package=work_package
								)
					else:
						tags = EquipmentTag.objects.none()
				elif bulk_mode == 'search':
					# Add tags matching search criteria
					search = form.cleaned_data.get('search_term', '')
					tags = EquipmentTag.objects.filter(
							project=work_package.project
							).filter(
							Q(tag_number__icontains=search) |
							Q(description__icontains=search)
							).exclude(
							work_package_items__work_package=work_package
							)
				elif bulk_mode == 'type':
					# Add all tags of a specific type
					equipment_type = form.cleaned_data.get('equipment_type')
					if equipment_type:
						tags = EquipmentTag.objects.filter(
								project=work_package.project,
								equipment_type=equipment_type
								).exclude(
								work_package_items__work_package=work_package
								)
					else:
						tags = EquipmentTag.objects.none()
				elif bulk_mode == 'status':
					# Add all tags with a specific status
					status = form.cleaned_data.get('tag_status')
					if status:
						tags = EquipmentTag.objects.filter(
								project=work_package.project,
								status=status
								).exclude(
								work_package_items__work_package=work_package
								)
					else:
						tags = EquipmentTag.objects.none()
				else:
					tags = EquipmentTag.objects.none()
				
				# Get starting sequence number
				last_sequence = work_package.items.order_by('-sequence_number').first()
				sequence = (last_sequence.sequence_number + 1) if last_sequence else 1
				
				# Add tags
				for tag in tags:
					if not WorkPackageItem.objects.filter(
							work_package=work_package,
							equipment_tag=tag
							).exists():
						WorkPackageItem.objects.create(
								work_package=work_package,
								equipment_tag=tag,
								sequence_number=sequence
								)
						sequence += 1
						added_count += 1
					else:
						skipped_count += 1
			
			if added_count > 0:
				messages.success(
						request,
						f'Successfully added {added_count} equipment tag(s) to the work package.'
						)
			if skipped_count > 0:
				messages.warning(
						request,
						f'{skipped_count} tag(s) were already in the work package and were skipped.'
						)
			if added_count == 0 and skipped_count == 0:
				messages.info(request, 'No tags were found to add.')
			
			return redirect('construction:work_package_detail', pk=work_package.pk)
	else:
		form = WorkPackageItemBulkForm(work_package_id=work_package_id)
	
	context = {
			'form': form,
			'work_package': work_package,
			'page_title': f'Bulk Add Tags - {work_package.code}',
			'available_tags': EquipmentTag.objects.filter(
					project=work_package.project
					).exclude(
					work_package_items__work_package=work_package
					).select_related('area').order_by('tag_number'),
			'areas': Area.objects.filter(project=work_package.project),
			'systems': System.objects.filter(project=work_package.project),
			'existing_items': work_package.items.select_related('equipment_tag').order_by('sequence_number'),
			}
	
	return render(request, 'construction/work_package_item_bulk_form.html', context)


class WorkPackageItemDeleteView(LoginRequiredMixin, generic.DeleteView):
	"""Remove an equipment tag from a work package."""
	model = WorkPackageItem
	template_name = 'construction/work_package_item_confirm_delete.html'
	success_message = "Equipment tag removed from work package successfully."
	
	def get_success_url(self):
		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['work_package'] = self.object.work_package
		context['equipment_tag'] = self.object.equipment_tag
		return context
	
	def delete(self, request, *args, **kwargs):
		obj = self.get_object()
		messages.success(
				request,
				f'Tag "{obj.equipment_tag.tag_number}" removed from work package.'
				)
		return super().delete(request, *args, **kwargs)


def work_package_item_toggle_complete_view(request, pk):
	"""Toggle the completion status of a work package item."""
	item = get_object_or_404(WorkPackageItem, pk=pk)
	
	# Toggle completion
	item.is_complete = not item.is_complete
	item.save()
	
	# Update work package progress
	work_package = item.work_package
	total_items = work_package.items.count()
	completed_items = work_package.items.filter(is_complete=True).count()
	
	if total_items > 0:
		work_package.percent_complete = int((completed_items / total_items) * 100)
		
		# Auto-complete work package if all items done
		if work_package.percent_complete >= 100:
			work_package.status = 'COMP'
			work_package.actual_finish = work_package.actual_finish or timezone.now().date()
		
		work_package.save()
	
	status = "completed" if item.is_complete else "reopened"
	messages.success(
			request,
			f'Tag "{item.equipment_tag.tag_number}" marked as {status}.'
			)
	
	return redirect('construction:work_package_detail', pk=work_package.pk)


def work_package_item_reorder_view(request, work_package_id):
	"""Reorder work package items."""
	work_package = get_object_or_404(WorkPackage, pk=work_package_id)
	
	if request.method == 'POST':
		item_order = request.POST.getlist('item_order')
		
		if item_order:
			with transaction.atomic():
				for index, item_id in enumerate(item_order, start=1):
					WorkPackageItem.objects.filter(
							pk=item_id,
							work_package=work_package
							).update(sequence_number=index)
			
			messages.success(request, 'Item order updated successfully.')
		
		return redirect('construction:work_package_detail', pk=work_package.pk)
	
	items = work_package.items.select_related('equipment_tag').order_by('sequence_number')
	
	return render(request, 'construction/work_package_item_reorder.html', {
			'work_package': work_package,
			'items': items,
			})


def ajax_search_available_tags(request, work_package_id):
	"""AJAX endpoint to search available tags for a work package."""
	work_package = get_object_or_404(WorkPackage, pk=work_package_id)
	search = request.GET.get('q', '')
	
	# Get tags not already in this work package
	existing_tag_ids = work_package.items.values_list('equipment_tag_id', flat=True)
	
	queryset = EquipmentTag.objects.filter(
			project=work_package.project
			).exclude(
			pk__in=existing_tag_ids
			)
	
	if search:
		queryset = queryset.filter(
				Q(tag_number__icontains=search) |
				Q(description__icontains=search)
				)
	
	# Apply optional filters
	area_id = request.GET.get('area')
	if area_id:
		queryset = queryset.filter(area_id=area_id)
	
	equipment_type = request.GET.get('equipment_type')
	if equipment_type:
		queryset = queryset.filter(equipment_type=equipment_type)
	
	results = []
	for tag in queryset.select_related('area')[:30]:
		results.append({
				'id': tag.pk,
				'tag_number': tag.tag_number,
				'description': tag.description[:100],
				'equipment_type': tag.get_equipment_type_display(),
				'status': tag.get_status_display(),
				'area': tag.area.code if tag.area else 'N/A',
				})
	
	return JsonResponse({'results': results})





class DailyProgressReportListView(LoginRequiredMixin, generic.ListView):
	model = DailyProgressReport
	template_name = 'construction/daily_report_list.html'
	context_object_name = 'reports'
	paginate_by = 25
	
	def get_queryset(self):
		queryset = DailyProgressReport.objects.select_related(
				'work_package__project',
				'work_package__area',
				'reported_by',
				'approved_by'
				).prefetch_related(
				'work_package__items__equipment_tag'
				)
		
		# Apply filters
		form = DailyReportSearchForm(self.request.GET)
		if form.is_valid():
			data = form.cleaned_data
			
			if data.get('project'):
				queryset = queryset.filter(work_package__project=data['project'])
			
			if data.get('work_package'):
				queryset = queryset.filter(work_package=data['work_package'])
			
			if data.get('area'):
				queryset = queryset.filter(work_package__area=data['area'])
			
			if data.get('reported_by'):
				queryset = queryset.filter(reported_by=data['reported_by'])
			
			if data.get('date_from'):
				queryset = queryset.filter(report_date__gte=data['date_from'])
			
			if data.get('date_to'):
				queryset = queryset.filter(report_date__lte=data['date_to'])
			
			if data.get('has_issues') == 'true':
				queryset = queryset.filter(
						issues_encountered__isnull=False
						).exclude(issues_encountered='')
			
			if data.get('is_approved') in ['true', 'false']:
				queryset = queryset.filter(is_approved=data['is_approved'] == 'true')
			
			if data.get('weather'):
				queryset = queryset.filter(
						weather_conditions__icontains=data['weather']
						)
			
			if data.get('search'):
				search = data['search']
				queryset = queryset.filter(
						Q(work_performed_description__icontains=search) |
						Q(issues_encountered__icontains=search) |
						Q(work_package__code__icontains=search) |
						Q(work_package__name__icontains=search) |
						Q(weather_conditions__icontains=search)
						)
		
		# Apply sorting
		sort = self.request.GET.get('sort', '-report_date')
		allowed_sorts = [
				'report_date', '-report_date',
				'work_package__code', '-work_package__code',
				'manpower_count', '-manpower_count',
				'hours_worked', '-hours_worked',
				'weather_conditions', '-weather_conditions',
				'created_at', '-created_at',
				]
		if sort in allowed_sorts:
			queryset = queryset.order_by(sort, '-created_at')
		
		return queryset
	
	def get_paginate_by(self, queryset):
		per_page = self.request.GET.get('per_page', '25')
		try:
			return min(int(per_page), 100)
		except ValueError:
			return 25
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Search form
		context['search_form'] = DailyReportSearchForm(self.request.GET)
		
		# View mode
		context['view_mode'] = self.request.GET.get('view', 'table')
		
		# Base queryset for statistics
		base_queryset = DailyProgressReport.objects.all()
		project_id = self.request.GET.get('project')
		if project_id:
			base_queryset = base_queryset.filter(work_package__project_id=project_id)
		
		# Statistics
		stats = base_queryset.aggregate(
				total_reports=Count('id'),
				total_manpower=Sum('manpower_count'),
				total_hours=Sum('hours_worked'),
				avg_manpower=Avg('manpower_count'),
				avg_hours=Avg('hours_worked')
				)
		
		context['total_reports'] = stats['total_reports'] or 0
		context['total_manpower'] = stats['total_manpower'] or 0
		context['total_hours'] = round(stats['total_hours'] or 0, 1)
		context['avg_manpower'] = round(stats['avg_manpower'] or 0, 1)
		context['avg_hours'] = round(stats['avg_hours'] or 0, 1)
		
		# Reports with issues
		context['reports_with_issues'] = base_queryset.filter(
				issues_encountered__isnull=False
				).exclude(issues_encountered='').count()
		
		# Pending approval
		context['pending_approval'] = base_queryset.filter(is_approved=False).count()
		
		# This week's reports
		today = timezone.now().date()
		week_start = today - timedelta(days=today.weekday())
		week_reports = base_queryset.filter(report_date__gte=week_start)
		context['week_reports'] = week_reports.count()
		context['week_hours'] = round(week_reports.aggregate(
				total=Sum('hours_worked')
				)['total'] or 0, 1)
		
		# Today's reports
		context['today_reports'] = base_queryset.filter(report_date=today).count()
		
		# Weather summary
		context['weather_summary'] = base_queryset.values(
				'weather_conditions'
				).annotate(
				count=Count('id')
				).exclude(
				weather_conditions__isnull=True
				).exclude(
				weather_conditions=''
				).order_by('-count')[:10]
		
		# Work package summary
		context['wp_summary'] = base_queryset.values(
				'work_package__code',
				'work_package__name',
				'work_package_id'
				).annotate(
				report_count=Count('id'),
				total_hours=Sum('hours_worked'),
				total_manpower=Sum('manpower_count')
				).order_by('-report_count')[:10]
		
		# Daily hours for last 14 days (for chart)
		daily_data = []
		for i in range(13, -1, -1):
			day = today - timedelta(days=i)
			day_stats = base_queryset.filter(report_date=day).aggregate(
					reports=Count('id'),
					hours=Sum('hours_worked'),
					manpower=Sum('manpower_count')
					)
			daily_data.append({
					'date': day,
					'day_name': day.strftime('%a'),
					'day_number': day.strftime('%d'),
					'reports': day_stats['reports'] or 0,
					'hours': float(day_stats['hours'] or 0),
					'manpower': day_stats['manpower'] or 0,
					'is_today': day == today,
					'is_weekend': day.weekday() >= 5
					})
		context['daily_data'] = daily_data
		
		# Projects for filter dropdown
		context['projects'] = Project.objects.all()
		
		# Active work packages
		context['work_packages'] = WorkPackage.objects.filter(
				status__in=['IPRO', 'MOB', 'NSTA']
				).select_related('project').order_by('code')
		
		# Areas for filter
		context['areas'] = Area.objects.all()
		
		# # Current date
		# context['today'] = today
		# max_height_px = 120  # Maximum bar height in pixels
		#
		# for day in daily_hours:
		# 	if max_hours > 0:
		# 		day['bar_height'] = max(3, int((day['hours'] / max_hours) * max_height_px))
		# 	else:
		# 		day['bar_height'] = 3
		return context
class DailyProgressReportListView2(LoginRequiredMixin, generic.ListView):
	model = DailyProgressReport
	template_name = 'construction/daily_report_list2.html'
	context_object_name = 'reports'
	paginate_by = 25
	
	def get_queryset(self):
		queryset = DailyProgressReport.objects.select_related(
				'work_package__project', 'work_package__area', 'reported_by'
				)
		
		work_package_id = self.request.GET.get('work_package')
		if work_package_id:
			queryset = queryset.filter(work_package_id=work_package_id)
		
		project_id = self.request.GET.get('project')
		if project_id:
			queryset = queryset.filter(work_package__project_id=project_id)
		
		date_from = self.request.GET.get('date_from')
		if date_from:
			queryset = queryset.filter(report_date__gte=date_from)
		
		date_to = self.request.GET.get('date_to')
		if date_to:
			queryset = queryset.filter(report_date__lte=date_to)
		
		return queryset.order_by('-report_date', '-created_at')
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Get base queryset for statistics
		base_queryset = DailyProgressReport.objects.all()
		
		work_package_id = self.request.GET.get('work_package')
		if work_package_id:
			base_queryset = base_queryset.filter(work_package_id=work_package_id)
		
		project_id = self.request.GET.get('project')
		if project_id:
			base_queryset = base_queryset.filter(work_package__project_id=project_id)
		
		# Statistics
		stats = base_queryset.aggregate(
				total_reports=Count('id'),
				total_manpower=Sum('manpower_count'),
				total_hours=Sum('hours_worked'),
				)
		context['total_reports'] = stats['total_reports'] or 0
		context['total_manpower'] = stats['total_manpower'] or 0
		context['total_hours'] = stats['total_hours'] or 0
		
		# DAILY CHART DATA
		today = timezone.now().date()
		daily_data = []
		max_hours = 1  # Start with 1 to avoid division by zero
		
		for i in range(13, -1, -1):
			day = today - timedelta(days=i)
			day_reports = base_queryset.filter(report_date=day)
			
			day_stats = day_reports.aggregate(
					hours=Sum('hours_worked'),
					manpower=Sum('manpower_count'),
					reports=Count('id')
					)
			
			hours = float(day_stats['hours'] or 0)
			
			daily_data.append({
					'date': day,
					'day_name': day.strftime('%a'),
					'day_number': day.strftime('%d'),
					'hours': hours,
					'manpower': int(day_stats['manpower'] or 0),
					'reports': day_stats['reports'] or 0,
					'is_today': day == today,
					'is_weekend': day.weekday() >= 5,
					})
			
			if hours > max_hours:
				max_hours = hours
		
		# Calculate pixel heights (max 120px for tallest bar)
		max_height = 120
		for day in daily_data:
			if day['hours'] > 0:
				day['bar_height'] = max(4, int((day['hours'] / max_hours) * max_height))
			else:
				day['bar_height'] = 1
		
		context['daily_data'] = daily_data
		context['max_hours'] = max_hours
		context['work_packages'] = WorkPackage.objects.filter(status__in=['IPRO', 'MOB']).select_related('project')
		context['projects'] = Project.objects.all()
		
		return context
def daily_report_approve_view(request, pk):
	"""
	Approve a daily progress report.
	Can be called via AJAX or regular form submission.
	"""
	report = get_object_or_404(DailyProgressReport, pk=pk)
	
	# Check if already approved
	if report.is_approved:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
					'success': False,
					'message': 'This report is already approved.',
					'status': 'already_approved'
					})
		messages.warning(request, 'This report is already approved.')
		return redirect_to_referer(request, 'construction:daily_report_list')
	
	# Approve the report
	report.is_approved = True
	report.approved_by = request.user
	report.save(update_fields=['is_approved', 'approved_by', 'updated_at'])
	
	# AJAX response
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
				'success': True,
				'message': 'Report approved successfully.',
				'approved_by': request.user.get_full_name() or request.user.username,
				'approved_date': timezone.now().strftime('%b %d, %Y %H:%M'),
				'report_id': report.pk
				})
	
	# Regular response
	messages.success(
			request,
			f'Daily report for {report.report_date.strftime("%B %d, %Y")} was approved successfully.'
			)
	
	return redirect_to_referer(request, 'construction:daily_report_list')


def daily_report_unapprove_view(request, pk):
	"""
	Unapprove a daily progress report (revert to pending).
	"""
	report = get_object_or_404(DailyProgressReport, pk=pk)
	
	# Check if already pending
	if not report.is_approved:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
					'success': False,
					'message': 'This report is already pending approval.',
					'status': 'already_pending'
					})
		messages.warning(request, 'This report is already pending approval.')
		return redirect_to_referer(request, 'construction:daily_report_list')
	
	# Unapprove the report
	report.is_approved = False
	report.approved_by = None
	report.save(update_fields=['is_approved', 'approved_by', 'updated_at'])
	
	# AJAX response
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
				'success': True,
				'message': 'Report unapproved successfully.',
				'report_id': report.pk
				})
	
	# Regular response
	messages.success(
			request,
			f'Daily report for {report.report_date.strftime("%B %d, %Y")} was unapproved.'
			)
	
	return redirect_to_referer(request, 'construction:daily_report_list')



def daily_report_bulk_approve_view(request):
	"""
	Bulk approve multiple daily progress reports.
	"""
	report_ids = request.POST.getlist('report_ids')
	
	if not report_ids:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
					'success': False,
					'message': 'No reports selected.'
					})
		messages.error(request, 'No reports selected for approval.')
		return redirect('construction:daily_report_list')
	
	# Filter reports that are not yet approved
	reports = DailyProgressReport.objects.filter(
			pk__in=report_ids,
			is_approved=False
			)
	
	approved_count = reports.count()
	skipped_count = len(report_ids) - approved_count
	
	# Bulk approve
	reports.update(
			is_approved=True,
			approved_by=request.user,
			updated_at=timezone.now()
			)
	
	# AJAX response
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({
				'success': True,
				'message': f'{approved_count} report(s) approved successfully.',
				'approved_count': approved_count,
				'skipped_count': skipped_count
				})
	
	# Regular response
	if approved_count > 0:
		messages.success(
				request,
				f'{approved_count} report(s) approved successfully.'
				)
	if skipped_count > 0:
		messages.warning(
				request,
				f'{skipped_count} report(s) were already approved and skipped.'
				)
	
	return redirect('construction:daily_report_list')


def daily_report_approval_status_view(request, pk):
	"""
	Get the approval status of a report (for AJAX polling).
	"""
	report = get_object_or_404(DailyProgressReport, pk=pk)
	
	return JsonResponse({
			'report_id': report.pk,
			'is_approved': report.is_approved,
			'approved_by': report.approved_by.get_full_name() if report.approved_by else None,
			'approved_date': report.updated_at.strftime('%b %d, %Y %H:%M') if report.is_approved else None,
			'report_date': report.report_date.strftime('%B %d, %Y'),
			'work_package': report.work_package.code,
			})


def redirect_to_referer(request, fallback_url):
	"""
	Redirect to the referring page or fallback URL.
	"""
	referer = request.META.get('HTTP_REFERER')
	if referer:
		return redirect(referer)
	return redirect(fallback_url)


class DailyProgressReportCreateView2(LoginRequiredMixin, ListView):
	model = Employee
	template_name = 'construction/employee_simple_list.html'
	context_object_name = 'employees'
	ordering = ['company', 'last_name', 'first_name']
	
	def get_queryset(self):
		queryset = super().get_queryset()
		# Company filter from GET (or from POST if we store it)
		company = self.request.GET.get('company') or self.request.POST.get('company')
		if company:
			queryset = queryset.filter(company=company)
		return queryset
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		# Companies for dropdown
		context['companies'] = Employee.objects.values_list('company', flat=True).distinct().order_by('company')
		context['selected_company'] = self.request.GET.get('company', '') or self.request.POST.get('company', '')
		# Date selection
		selected_date = self.request.GET.get('report_date', '') or self.request.POST.get('report_date', '')
		context['selected_date'] = selected_date
		# Working employee IDs – empty on GET, filled on POST
		context['working_employee_ids'] = []
		return context
	
	def post(self, request, *args, **kwargs):
		# Get the list of checked employee IDs from the form
		working_ids = request.POST.getlist('working_employees')  # list of strings
		working_ids = [int(pk) for pk in working_ids]
		
		# For demonstration – you can later save these to a model
		messages.success(request, f"Captured {len(working_ids)} working employees: {working_ids}")
		working_employees = Employee.objects.filter(pk__in=working_ids)
		# 1. Capture the selected date
		report_date_str = request.POST.get('report_date', '').strip()
		report_date = timezone.now()
		if report_date_str:
			try:
				report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
			except ValueError:
				messages.error(request, f"Invalid date format: '{report_date_str}'. Please use YYYY-MM-DD.")
		for working_employee in working_employees:
				Timesheet.objects.create(employee=working_employee,date=report_date)
		timesheets_to_remove = Timesheet.objects.none()
		if report_date:
			timesheets_to_remove = Timesheet.objects.filter(
					date=report_date
					).exclude(
					employee__in=working_employees
					)
			for timesheet in timesheets_to_remove:
				timesheet.delete()
		all_timesheets=Timesheet.objects.filter(date=report_date)
		print(all_timesheets)
			# Re‑render the page with the company filter preserved and toggles on
			# We'll add the working_ids to context so the switches stay checked
			# context = self.get_context_data()
			# context['working_employee_ids'] = working_ids
			# Manually set the object_list (queryset) because post doesn't call get
			# self.object_list = self.get_queryset()
			# context['employees'] = self.object_list
		return redirect('construction:daily_report_create2')

class DailyProgressReportCreateView3( generic.CreateView):
	"""Create a daily progress report – only for the user's company employees."""
	model = DailyProgressReport
	form_class = DailyProgressReportForm2
	template_name = 'construction/daily_report_form2.html'
	success_message = "Daily progress report was created successfully."
	
	# ---------- User company check ----------
	def test_func(self):
		"""Ensure the logged-in user has an associated Employee record."""
		try:
			self.user_employee = Employee.objects.get(user=self.request.user)
			return True
		except Employee.DoesNotExist:
			return False
	
	def handle_no_permission(self):
		messages.error(self.request, "Your account is not linked to an employee profile. Please contact an administrator.")
		return redirect('core:dashboard')
	
	def get_user_company(self):
		"""Get the company of the logged-in user."""
		if not hasattr(self, 'user_employee'):
			self.user_employee = Employee.objects.get(user=self.request.user)
		return self.user_employee.company
	
	# ---------- Standard CreateView methods ----------
	def get_success_url(self):
		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
	
	def get_initial(self):
		initial = super().get_initial()
		work_package_id = self.kwargs.get('work_package_id') or self.request.GET.get('work_package')
		if work_package_id:
			initial['work_package'] = get_object_or_404(WorkPackage, pk=work_package_id)
		initial['report_date'] = timezone.now().date()
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = True
		context['page_title'] = 'Create Daily Progress Report'
		
		user_company = self.get_user_company()
		work_package_id = self.kwargs.get('work_package_id') or self.request.GET.get('work_package')
		
		if work_package_id:
			work_package = get_object_or_404(WorkPackage, pk=work_package_id)
			context['work_package'] = work_package
			
			# Get equipment tags (unchanged)
			context['work_package_items'] = work_package.items.select_related('equipment_tag').order_by('sequence_number')
			
			# Previous reports
			context['previous_reports'] = DailyProgressReport.objects.filter(
					work_package=work_package
					).select_related('reported_by').order_by('-report_date')[:5]
			
			today = timezone.now().date()
			context['today_report'] = DailyProgressReport.objects.filter(
					work_package=work_package,
					report_date=today
					).first()
			
			# ------ FILTER EMPLOYEES BY USER'S COMPANY ------
			employees = Employee.objects.filter(
					is_active=True,
					company=user_company
					).order_by('last_name', 'first_name')
			context['employees'] = employees  # single list, no grouping needed
			
			# Today's working employees (pre‑check)
			if context['today_report']:
				today_working_ids = DailyProcessReportEmployees.objects.filter(
						daily_report=context['today_report'],
						is_working=True
						).values_list('employee_id', flat=True)
				context['today_working_employee_ids'] = list(today_working_ids)
			else:
				context['today_working_employee_ids'] = []
			
			# Yesterday's working employees for quick copy
			if context['previous_reports']:
				yesterday_report = context['previous_reports'].first()
				yesterday_working = DailyProcessReportEmployees.objects.filter(
						daily_report=yesterday_report,
						is_working=True
						).values_list('employee_id', flat=True)
				context['yesterday_working_employee_ids'] = list(yesterday_working)
		
		# Weather options
		context['weather_options'] = [
				'Sunny', 'Partly Cloudy', 'Cloudy', 'Overcast',
				'Light Rain', 'Rain', 'Heavy Rain', 'Thunderstorm',
				'Snow', 'Windy', 'Foggy', 'Dust Storm'
				]
		return context
	
	@transaction.atomic
	def form_valid(self, form):
		user_company = self.get_user_company()
		form.instance.reported_by = self.request.user
		self.object = form.save()
		
		# Get submitted employee IDs and validate they belong to user's company
		working_employee_ids = self.request.POST.getlist('working_employees')
		not_working_employee_ids = self.request.POST.getlist('not_working_employees')
		
		# Validate – only keep IDs that actually belong to the user's company
		valid_working_ids = Employee.objects.filter(
				pk__in=working_employee_ids,
				company=user_company,
				is_active=True
				).values_list('id', flat=True)
		
		valid_not_working_ids = Employee.objects.filter(
				pk__in=not_working_employee_ids,
				company=user_company,
				is_active=True
				).values_list('id', flat=True)
		
		# Process working employees
		for emp_id in valid_working_ids:
			DailyProcessReportEmployees.objects.update_or_create(
					employee_id=emp_id,
					daily_report=self.object,
					defaults={'is_working': True}
					)
		
		# Process not working employees
		for emp_id in valid_not_working_ids:
			DailyProcessReportEmployees.objects.update_or_create(
					employee_id=emp_id,
					daily_report=self.object,
					defaults={'is_working': False}
					)
		
		# Update work package progress
		self.update_work_package_progress(form)
		
		messages.success(
				self.request,
				f'Daily report created with {len(valid_working_ids)} employee(s) working.'
				)
		return redirect(self.get_success_url())
	
	def update_work_package_progress(self, form):
		work_package = form.cleaned_data['work_package']
		if work_package.status == 'NSTA':
			work_package.status = 'IPRO'
			work_package.actual_start = work_package.actual_start or form.cleaned_data['report_date']
			work_package.save()