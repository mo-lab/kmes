from datetime import timezone, timedelta

from django.db.models import Q, Count, Case, When, Value, CharField,Sum
from django.http import HttpResponse
# views.py
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from django.views import generic
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Project, Area, System, EquipmentTag
from .forms import ProjectForm, AreaForm, SystemForm, EquipmentTagForm, EquipmentTagFilterForm,SystemSearchForm
from construction.models import WorkPackage,DailyProgressReport,WorkPackageItem
from commissioning.models import PunchItem
from documents.models import Document
from resources.models import Timesheet
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import EquipmentTag, EquipmentLocation, EquipmentLocationImage
from .forms import (
	EquipmentLocationForm,
	EquipmentLocationImageForm,
	EquipmentLocationSearchForm
	)
class ProjectCreateView(LoginRequiredMixin, generic.CreateView):
	"""Create a new project."""
	model = Project
	form_class = ProjectForm
	template_name = 'core/project_form.html'
	success_message = "Project '%(name)s' was created successfully."
	
	def get_success_url(self):
		if self.request.POST.get('save_add_another'):
			return reverse('core:project_create')
		return reverse('core:project-detail', kwargs={'pk': self.object.pk})
	
	def get_initial(self):
		initial = super().get_initial()
		
		# Set defaults
		initial['status'] = 'INIT'
		initial['start_date'] = timezone.now().date()
		
		# Auto-generate project code
		initial['code'] = self.generate_project_code()
		
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = True
		context['page_title'] = 'Create New Project'
		
		# Recent projects for reference
		context['recent_projects'] = Project.objects.order_by('-created_at')[:5]
		
		# Project statistics
		context['total_projects'] = Project.objects.count()
		context['active_projects'] = Project.objects.filter(
				status__in=['EXEC', 'COMM']
				).count()
		context['completed_projects'] = Project.objects.filter(status='CLSD').count()
		
		# Location suggestions
		context['location_suggestions'] = Project.objects.values_list(
				'location', flat=True
				).distinct().order_by('location')[:10]
		
		return context
	
	def form_valid(self, form):
		# Check for duplicate code
		code = form.cleaned_data.get('code')
		if Project.objects.filter(code=code).exists():
			messages.warning(
					self.request,
					f'Project code "{code}" already exists. A new code has been generated.'
					)
			form.instance.code = self.generate_project_code()
		
		messages.success(
				self.request,
				self.success_message % {'name': form.cleaned_data['name']}
				)
		
		return super().form_valid(form)
	
	def form_invalid(self, form):
		messages.error(self.request, 'Please correct the errors below.')
		return super().form_invalid(form)
	
	def generate_project_code(self):
		"""Generate a unique project code."""
		prefix = 'PRJ'
		year = timezone.now().strftime('%y')
		
		# Find the latest project code
		last_project = Project.objects.filter(
				code__startswith=f'{prefix}-{year}'
				).order_by('-code').first()
		
		if last_project:
			try:
				last_num = int(last_project.code.split('-')[-1])
				new_num = last_num + 1
			except (ValueError, IndexError):
				new_num = 1
		else:
			new_num = 1
		
		return f'{prefix}-{year}-{new_num:03d}'


class ProjectUpdateView(LoginRequiredMixin, generic.UpdateView):
	"""Update an existing project."""
	model = Project
	form_class = ProjectForm
	template_name = 'core/project_form.html'
	success_message = "Project '%(name)s' was updated successfully."
	
	def get_success_url(self):
		return reverse('core:project_detail', kwargs={'pk': self.object.pk})
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = False
		context['page_title'] = f'Edit Project: {self.object.name}'
		
		# Project stats
		project = self.get_object()
		context['project_areas_count'] = project.areas.count()
		context['project_systems_count'] = project.systems.count()
		context['project_equipment_count'] = project.equipment_tags.count()
		context['project_documents_count'] = project.documents.count()
		context['project_work_packages_count'] = project.work_packages.count()
		
		return context
	
	def form_valid(self, form):
		# Track status changes
		old_instance = Project.objects.get(pk=self.object.pk)
		new_status = form.cleaned_data.get('status')
		old_status = old_instance.status
		
		# Auto-set actual completion date
		if new_status == 'CLSD' and old_status != 'CLSD':
			if not form.instance.actual_completion_date:
				form.instance.actual_completion_date = timezone.now().date()
				messages.info(self.request, 'Actual completion date has been set to today.')
		
		messages.success(
				self.request,
				self.success_message % {'name': form.cleaned_data['name']}
				)
		
		return super().form_valid(form)


class AreaCreateView(LoginRequiredMixin, CreateView):
	model = Area
	form_class = AreaForm
	template_name = "core/area_form.html"
	
	def dispatch(self, request, *args, **kwargs):
		self.project = None
		project_pk = kwargs.get("project_pk")
		if project_pk:
			self.project = get_object_or_404(Project, pk=project_pk)
		return super().dispatch(request, *args, **kwargs)
	
	def get_initial(self):
		initial = super().get_initial()
		if self.project:
			initial["project"] = self.project
		return initial
	
	def get_form_kwargs(self):
		kw = super().get_form_kwargs()
		# If you want to limit choices in the form (e.g., project dropdown), pass project
		if self.project:
			kw.setdefault("initial", {})["project"] = self.project
		return kw
	
	def form_valid(self, form):
		# If project was provided in URL, ensure the created Area is linked to it
		if self.project:
			form.instance.project = self.project
		return super().form_valid(form)
	
	def get_success_url(self):
		# Redirect to project detail or area list; adjust as needed
		return reverse("core:project-detail", kwargs={"pk": self.object.project.pk})

class SystemCreateView(LoginRequiredMixin, generic.CreateView):
	"""Create a new system with optional equipment tags."""
	model = System
	form_class = SystemForm
	template_name = 'core/system_form.html'
	success_message = "System '%(code)s - %(name)s' was created successfully."
	
	def get_success_url(self):
		if self.request.POST.get('save_add_another'):
			return reverse('core:system_create')
		return reverse('core:system_detail', kwargs={'pk': self.object.pk})
	
	def get_initial(self):
		initial = super().get_initial()
		
		# Pre-fill from URL parameters
		project_id = self.kwargs.get('project_id') or self.request.GET.get('project')
		if project_id:
			initial['project'] = get_object_or_404(Project, pk=project_id)
		
		# Auto-generate system code
		if project_id:
			initial['code'] = self.generate_system_code(project_id)
		
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = True
		context['page_title'] = 'Create New System'
		
		# Get project for context
		project_id = self.kwargs.get('project_id') or self.request.GET.get('project')
		if project_id:
			project = get_object_or_404(Project, pk=project_id)
			context['project'] = project
			
			# Available equipment tags for this project
			context['available_tags'] = EquipmentTag.objects.filter(
					project_id=project_id
					).select_related('area').order_by('tag_number')
			
			# Tags grouped by equipment type
			context['tags_by_type'] = {}
			for tag in context['available_tags']:
				type_display = tag.get_equipment_type_display()
				if type_display not in context['tags_by_type']:
					context['tags_by_type'][type_display] = []
				context['tags_by_type'][type_display].append(tag)
		
		# Recent systems for reference
		context['recent_systems'] = System.objects.select_related('project').order_by('-created_at')[:5]
		
		# Equipment type options
		context['equipment_types'] = EquipmentTag.EquipmentType.choices
		
		# Existing system codes for reference
		if project_id:
			context['existing_codes'] = System.objects.filter(
					project_id=project_id
					).values_list('code', flat=True)
		
		return context
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		project_id = self.kwargs.get('project_id') or self.request.GET.get('project')
		if project_id:
			kwargs['project_id'] = int(project_id)
		return kwargs
	
	# @transaction.atomic
	def form_valid(self, form):
		# Save the system
		self.object = form.save()
		
		# Handle equipment tag linking
		tag_ids = self.request.POST.getlist('equipment_tags')
		if tag_ids:
			self.link_equipment_tags(tag_ids)
		
		# Handle bulk add by type
		equipment_type = self.request.POST.get('bulk_add_type')
		if equipment_type and self.request.POST.get('add_all_type_tags'):
			self.add_all_type_tags(equipment_type)
		
		# Handle bulk add by search
		tag_search = self.request.POST.get('tag_search')
		if tag_search and self.request.POST.get('add_search_results'):
			self.add_search_results_tags(tag_search)
		
		messages.success(
				self.request,
				self.success_message % {
						'code': self.object.code,
						'name': self.object.name
						}
				)
		
		# Show count of linked tags
		tag_count = EquipmentTag.objects.filter(system=self.object).count()
		if tag_count > 0:
			messages.info(
					self.request,
					f'{tag_count} equipment tag(s) linked to this system.'
					)
		
		return redirect(self.get_success_url())
	
	def form_invalid(self, form):
		messages.error(self.request, 'Please correct the errors below.')
		return super().form_invalid(form)
	
	def link_equipment_tags(self, tag_ids):
		"""Link selected equipment tags to this system."""
		count = EquipmentTag.objects.filter(
				pk__in=tag_ids,
				project_id=self.object.project_id
				).update(system=self.object)
		return count
	
	def add_all_type_tags(self, equipment_type):
		"""Add all tags of a specific type to this system."""
		count = EquipmentTag.objects.filter(
				project_id=self.object.project_id,
				equipment_type=equipment_type,
				system__isnull=True
				).update(system=self.object)
		return count
	
	def add_search_results_tags(self, search_term):
		"""Add tags matching search criteria to this system."""
		count = EquipmentTag.objects.filter(
				project_id=self.object.project_id,
				system__isnull=True
				).filter(
				Q(tag_number__icontains=search_term) |
				Q(description__icontains=search_term)
				)[:100].update(system=self.object)
		return count
	
	def generate_system_code(self, project_id):
		"""Generate a unique system code."""
		try:
			project = Project.objects.get(pk=project_id)
			project_prefix = project.code[:4].upper() if project.code else 'SYS'
		except Project.DoesNotExist:
			project_prefix = 'SYS'
		
		# Count existing systems for this project
		count = System.objects.filter(project_id=project_id).count() + 1
		
		return f"{project_prefix}-SYS-{count:03d}"


class SystemUpdateView(LoginRequiredMixin, generic.UpdateView):
	"""Update an existing system."""
	model = System
	form_class = SystemForm
	template_name = 'core/system_form.html'
	success_message = "System '%(code)s - %(name)s' was updated successfully."
	
	def get_success_url(self):
		return reverse('core:system_detail', kwargs={'pk': self.object.pk})
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = False
		context['page_title'] = f'Edit System: {self.object.code}'
		context['project'] = self.object.project
		
		# Linked equipment tags
		context['linked_tags'] = EquipmentTag.objects.filter(
				system=self.object
				).select_related('area').order_by('tag_number')
		
		# Available tags not yet linked to any system (or linked to this one)
		context['available_tags'] = EquipmentTag.objects.filter(
				project=self.object.project
				).filter(
				Q(system__isnull=True) | Q(system=self.object)
				).select_related('area').order_by('tag_number')
		
		# Tags grouped by type
		context['tags_by_type'] = {}
		for tag in context['available_tags']:
			type_display = tag.get_equipment_type_display()
			if type_display not in context['tags_by_type']:
				context['tags_by_type'][type_display] = []
			context['tags_by_type'][type_display].append(tag)
		
		return context
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		if self.object.project_id:
			kwargs['project_id'] = self.object.project_id
		return kwargs
	
	# @transaction.atomic
	def form_valid(self, form):
		self.object = form.save()
		
		# Handle adding new tags
		tag_ids = self.request.POST.getlist('equipment_tags')
		if tag_ids:
			EquipmentTag.objects.filter(
					pk__in=tag_ids,
					project_id=self.object.project_id
					).update(system=self.object)
		
		# Handle removing tags
		remove_tag_ids = self.request.POST.getlist('remove_tags')
		if remove_tag_ids:
			EquipmentTag.objects.filter(
					pk__in=remove_tag_ids,
					system=self.object
					).update(system=None)
		
		messages.success(
				self.request,
				self.success_message % {
						'code': self.object.code,
						'name': self.object.name
						}
				)
		
		return redirect(self.get_success_url())


class SystemDetailView(LoginRequiredMixin, generic.DetailView):
	"""View system details with equipment tags, commissioning status, and related items."""
	model = System
	template_name = 'core/system_detail.html'
	context_object_name = 'system'
	
	def get_queryset(self):
		return System.objects.select_related('project').prefetch_related(
				'equipment_tags__area',
				'equipment_tags__tag_documents',
				'commissioning_phases__test_procedures__test_records',
				'work_packages',
				'punch_items'
				)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		system = self.get_object()
		
		# Equipment Tags
		equipment_tags = system.equipment_tags.select_related(
				'area', 'parent_tag'
				).prefetch_related(
				'tag_documents',
				'punch_items',
				'installation_checks'
				).annotate(
				document_count=Count('tag_documents', distinct=True),
				open_punch_count=Count(
						Case(
								When(punch_items__status__in=['OPEN', 'IPRO'], then=1),
								output_field=CharField(),
								),
						distinct=True
						)
				).order_by('tag_number')
		
		context['equipment_tags'] = equipment_tags
		context['total_equipment'] = equipment_tags.count()
		
		# Equipment statistics
		context['installed_equipment'] = equipment_tags.filter(status='INST').count()
		context['commissioned_equipment'] = equipment_tags.filter(status='COMM').count()
		context['defective_equipment'] = equipment_tags.filter(status='DEF').count()
		context['delivered_equipment'] = equipment_tags.filter(status='DLVD').count()
		
		# Equipment grouped by type
		context['equipment_by_type'] = equipment_tags.values(
				'equipment_type'
				).annotate(
				count=Count('id')
				).order_by('-count')
		
		# Equipment grouped by area
		context['equipment_by_area'] = equipment_tags.values(
				'area__code', 'area__name', 'area_id'
				).annotate(
				count=Count('id')
				).order_by('area__code')
		
		# Commissioning
		commissioning = system.commissioning_phases.first()
		context['commissioning'] = commissioning
		
		if commissioning:
			# Test procedures
			test_procedures = commissioning.test_procedures.prefetch_related(
					'test_records', 'equipment_tags'
					).annotate(
					record_count=Count('test_records'),
					latest_result=Case(
							When(test_records__isnull=False, then=Value('PASS')),
							default=Value('NONE'),
							output_field=CharField()
							)
					).order_by('code')
			
			context['test_procedures'] = test_procedures
			context['total_test_procedures'] = test_procedures.count()
			
			# Test statistics
			test_stats = test_procedures.aggregate(
					total_tests=Count('test_records'),
					passed_tests=Count(
							Case(
									When(test_records__result='PASS', then=1),
									output_field=CharField(),
									)
							),
					failed_tests=Count(
							Case(
									When(test_records__result='FAIL', then=1),
									output_field=CharField(),
									)
							)
					)
			context['test_stats'] = test_stats
			
			# Calculate commissioning progress
			if context['total_test_procedures'] > 0:
				completed_procedures = TestRecord.objects.filter(
						test_procedure__commissioning_system=commissioning,
						result='PASS'
						).values('test_procedure').distinct().count()
				context['commissioning_progress'] = int(
						(completed_procedures / context['total_test_procedures']) * 100
						)
			else:
				context['commissioning_progress'] = 0
		
		# Punch Items
		punch_items = system.punch_items.select_related(
				'equipment_tag', 'raised_by', 'assigned_to'
				).order_by('-raised_date')
		
		context['punch_items'] = punch_items
		context['total_punch_items'] = punch_items.count()
		context['open_punch_items'] = punch_items.filter(
				status__in=['OPEN', 'IPRO']
				).count()
		context['critical_punch_items'] = punch_items.filter(
				category='A',
				status__in=['OPEN', 'IPRO']
				).count()
		
		# Work Packages
		work_packages = system.work_packages.select_related(
				'area', 'supervisor'
				).annotate(
				item_count=Count('items'),
				completed_items=Count(
						Case(
								When(items__is_complete=True, then=1),
								output_field=CharField(),
								)
						)
				).order_by('code')
		
		context['work_packages'] = work_packages
		context['total_work_packages'] = work_packages.count()
		context['active_work_packages'] = work_packages.filter(status='IPRO').count()
		
		# Documents linked to equipment in this system
		from documents.models import Document
		context['system_documents'] = Document.objects.filter(
				tag_documents__equipment_tag__system=system
				).distinct().order_by('-created_at')[:10]
		context['total_documents'] = Document.objects.filter(
				tag_documents__equipment_tag__system=system
				).distinct().count()
		
		# Recent activities
		context['activities'] = self.get_system_activities(system)
		
		# Status timeline
		context['status_timeline'] = self.get_status_timeline(system)
		
		return context
	
	def get_system_activities(self, system):
		"""Get recent activities for this system."""
		activities = []
		
		# Equipment status changes
		recent_tags = system.equipment_tags.order_by('-updated_at')[:5]
		for tag in recent_tags:
			activities.append({
					'icon': 'tag',
					'description': f'Equipment {tag.tag_number} status: {tag.get_status_display()}',
					'date': tag.updated_at,
					'type': 'equipment'
					})
		
		# Test records
		if hasattr(system, 'commissioning_phases'):
			for cs in system.commissioning_phases.all():
				for procedure in cs.test_procedures.all():
					for record in procedure.test_records.order_by('-start_datetime')[:3]:
						activities.append({
								'icon': 'clipboard-check',
								'description': f'Test {procedure.code} - {record.get_result_display()}',
								'date': record.start_datetime,
								'type': 'test'
								})
		
		# Punch items
		for punch in system.punch_items.order_by('-raised_date')[:3]:
			activities.append({
					'icon': 'flag',
					'description': f'Punch item {punch.punch_number} - {punch.get_status_display()}',
					'date': punch.raised_date,
					'type': 'punch'
					})
		
		# Sort by date
		activities.sort(key=lambda x: x['date'], reverse=True)
		return activities[:15]
	
	def get_status_timeline(self, system):
		"""Get status timeline for the system."""
		timeline = [
				{
						'stage': 'Design',
						'status': 'completed',
						'description': 'System defined and equipment specified'
						}
				]
		
		# Check equipment procurement
		if system.equipment_tags.filter(status__in=['DLVD', 'INST', 'COMM', 'HNDO']).exists():
			timeline.append({
					'stage': 'Procurement',
					'status': 'completed',
					'description': 'Equipment procured and delivered'
					})
		elif system.equipment_tags.filter(status='PROC').exists():
			timeline.append({
					'stage': 'Procurement',
					'status': 'in_progress',
					'description': 'Equipment being procured'
					})
		else:
			timeline.append({
					'stage': 'Procurement',
					'status': 'pending',
					'description': 'Equipment not yet ordered'
					})
		
		# Check installation
		installed_count = system.equipment_tags.filter(status__in=['INST', 'COMM', 'HNDO']).count()
		total_count = system.equipment_tags.count()
		
		if total_count > 0 and installed_count == total_count:
			timeline.append({
					'stage': 'Installation',
					'status': 'completed',
					'description': 'All equipment installed'
					})
		elif installed_count > 0:
			timeline.append({
					'stage': 'Installation',
					'status': 'in_progress',
					'description': f'{installed_count}/{total_count} equipment installed'
					})
		else:
			timeline.append({
					'stage': 'Installation',
					'status': 'pending',
					'description': 'Installation not started'
					})
		
		# Check commissioning
		commissioning = system.commissioning_phases.first()
		if commissioning:
			if commissioning.status == 'HNDO':
				timeline.append({
						'stage': 'Commissioning',
						'status': 'completed',
						'description': 'System handed over'
						})
			elif commissioning.status in ['HOT', 'RAMP', 'PERF']:
				timeline.append({
						'stage': 'Commissioning',
						'status': 'in_progress',
						'description': f'Commissioning in progress - {commissioning.get_status_display()}'
						})
			else:
				timeline.append({
						'stage': 'Commissioning',
						'status': 'in_progress',
						'description': f'Commissioning started - {commissioning.get_status_display()}'
						})
		else:
			timeline.append({
					'stage': 'Commissioning',
					'status': 'pending',
					'description': 'Commissioning not started'
					})
		
		return timeline
	

class EquipmentTagCreateView(LoginRequiredMixin, CreateView):
	model = EquipmentTag
	form_class = EquipmentTagForm
	template_name = "core/equipmenttag_form.html"
	
	def dispatch(self, request, *args, **kwargs):
		self.project = None
		project_pk = kwargs.get("project_pk")
		if project_pk:
			self.project = get_object_or_404(Project, pk=project_pk)
		return super().dispatch(request, *args, **kwargs)
	
	def get_initial(self):
		initial = super().get_initial()
		if self.project:
			initial["project"] = self.project
		return initial
	
	def get_form_kwargs(self):
		kw = super().get_form_kwargs()
		# Narrow parent_tag, area, system querysets to the selected project for better UX
		if self.project:
			kw.setdefault("initial", {})["project"] = self.project
			form = self.get_form_class()
		# We will set queryset restrictions after instantiating the form in get_form()
		return kw
	
	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		# If project is known, restrict related-object choices to that project
		if self.project:
			form.fields["project"].queryset = Project.objects.filter(pk=self.project.pk)
			form.fields["area"].queryset = form.fields["area"].queryset.filter(project=self.project)
			form.fields["system"].queryset = form.fields["system"].queryset.filter(project=self.project)
			form.fields["parent_tag"].queryset = form.fields["parent_tag"].queryset.filter(project=self.project)
		return form
	
	def form_valid(self, form):
		if self.project:
			form.instance.project = self.project
		return super().form_valid(form)
	
	def get_success_url(self):
		return reverse("core:project-detail", kwargs={"pk": self.object.project.pk})


class ProjectListView(generic.ListView):
	model = Project
	template_name = 'core/project_list.html'
	context_object_name = 'projects'
	paginate_by = 12
	
	def get_queryset(self):
		queryset = Project.objects.annotate(
				area_count=Count('areas', distinct=True),
				system_count=Count('systems', distinct=True),
				equipment_count=Count('equipment_tags', distinct=True)
				)
		
		# Search
		search = self.request.GET.get('search', '')
		if search:
			queryset = queryset.filter(
					Q(name__icontains=search) |
					Q(code__icontains=search) |
					Q(location__icontains=search) |
					Q(description__icontains=search)
					)
		
		# Status filter
		status = self.request.GET.get('status', '')
		if status:
			queryset = queryset.filter(status=status)
		
		# Sorting
		sort = self.request.GET.get('sort', '-created_at')
		allowed_sorts = ['name', '-name', 'created_at', '-created_at',
		                 'target_completion_date', '-target_completion_date']
		if sort in allowed_sorts:
			queryset = queryset.order_by(sort)
		
		return queryset
	
	def get_paginate_by(self, queryset):
		per_page = self.request.GET.get('per_page', '12')
		try:
			return int(per_page)
		except ValueError:
			return 12
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		queryset = Project.objects.all()
		
		# Quick stats
		context['total_count'] = queryset.count()
		context['in_progress_count'] = queryset.filter(status__in=['EXEC', 'COMM']).count()
		context['completed_count'] = queryset.filter(status='CLSD').count()
		context['planning_count'] = queryset.filter(status__in=['INIT', 'PLAN']).count()
		
		return context


class ProjectDetailView(generic.DetailView):
	model = Project
	template_name = 'core/project_detail.html'
	context_object_name = 'project'
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		project = self.get_object()
		
		# Areas with related counts
		context['areas'] = project.areas.annotate(
				equipment_count=Count('equipment_tags'),
				work_package_count=Count('work_packages')
				).all()
		
		# Systems with commissioning status
		context['systems'] = project.systems.prefetch_related(
				'commissioning_phases'
				).all()
		
		# Equipment tags (limited for display)
		context['equipment_tags'] = project.equipment_tags.select_related(
				'area', 'parent_tag'
				).order_by('tag_number')[:100]
		
		# Total equipment count
		context['equipment_count'] = project.equipment_tags.count()
		
		# Open punch items count
		
		context['punch_items_count'] = PunchItem.objects.filter(
				project=project,
				status__in=['OPEN', 'IPRO']
				).count()
		
		# Recent activities (you can implement this based on your needs)
		context['recent_activities'] = self.get_recent_activities(project)
		
		return context
	
	def get_recent_activities(self, project):
		"""Get recent activities across all related models."""
		activities = []
		
		# Recent documents
		recent_docs = project.documents.order_by('-created_at')[:3]
		for doc in recent_docs:
			activities.append(
					{
							'icon':        'file-earmark-text',
							'description': f'Document "{doc.title}" was {doc.get_status_display().lower()}',
							'timestamp':   doc.created_at
							}
					)
		
		# Recent work package updates
		
		recent_wps = WorkPackage.objects.filter(
				project=project
				).order_by('-updated_at')[:3]
		for wp in recent_wps:
			activities.append(
					{
							'icon':        'clipboard-check',
							'description': f'Work package "{wp.code}" status changed to {wp.get_status_display()}',
							'timestamp':   wp.updated_at
							}
					)
		
		# Recent equipment tag updates
		recent_tags = project.equipment_tags.order_by('-updated_at')[:3]
		for tag in recent_tags:
			activities.append(
					{
							'icon':        'tag',
							'description': f'Equipment tag "{tag.tag_number}" status: {tag.get_status_display()}',
							'timestamp':   tag.updated_at
							}
					)
		
		# Sort by timestamp and limit
		activities.sort(key=lambda x: x['timestamp'], reverse=True)
		return activities[:10]


class EquipmentTagListView(LoginRequiredMixin, generic.ListView):
	model = EquipmentTag
	template_name = 'core/equipment_tag_list.html'
	context_object_name = 'tags'
	paginate_by = 20
	
	def get_queryset(self):
		queryset = EquipmentTag.objects.select_related(
				'project', 'area', 'system', 'parent_tag'
				).prefetch_related(
				'child_tags',
				'tag_documents',
				'punch_items'
				).annotate(
				child_count=Count('child_tags', distinct=True),
				document_count=Count('tag_documents', distinct=True),
				open_punch_count=Count(
						Case(
								When(punch_items__status__in=['OPEN', 'IPRO'], then=1),
								output_field=CharField(),
								),
						distinct=True
						)
				)
		
		# Apply filters from the form
		form = EquipmentTagFilterForm(self.request.GET)
		if form.is_valid():
			data = form.cleaned_data
			
			if data.get('project'):
				queryset = queryset.filter(project=data['project'])
			
			if data.get('area'):
				queryset = queryset.filter(area=data['area'])
			
			if data.get('system'):
				queryset = queryset.filter(system=data['system'])
			
			if data.get('equipment_type'):
				queryset = queryset.filter(equipment_type=data['equipment_type'])
			
			if data.get('status'):
				queryset = queryset.filter(status=data['status'])
			
			if data.get('discipline'):
				queryset = queryset.filter(discipline=data['discipline'])
			
			if data.get('criticality'):
				queryset = queryset.filter(criticality=data['criticality'])
			
			if data.get('search'):
				search = data['search']
				queryset = queryset.filter(
						Q(tag_number__icontains=search) |
						Q(description__icontains=search) |
						Q(manufacturer__icontains=search) |
						Q(model_number__icontains=search) |
						Q(serial_number__icontains=search)
						)
			
			if data.get('parent_tag_only'):
				queryset = queryset.filter(parent_tag__isnull=data['parent_tag_only'] == 'true')
		
		# Apply sorting
		sort = self.request.GET.get('sort', 'tag_number')
		allowed_sorts = [
				'tag_number', '-tag_number',
				'description', '-description',
				'equipment_type', '-equipment_type',
				'status', '-status',
				'criticality', '-criticality',
				'created_at', '-created_at',
				'updated_at', '-updated_at',
				]
		if sort in allowed_sorts:
			queryset = queryset.order_by(sort)
		
		return queryset
	
	def get_paginate_by(self, queryset):
		per_page = self.request.GET.get('per_page', '20')
		try:
			return min(int(per_page), 100)  # Max 100 per page
		except ValueError:
			return 20
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Filter form
		context['filter_form'] = EquipmentTagFilterForm(self.request.GET)
		
		# View mode (card or table)
		context['view_mode'] = self.request.GET.get('view', 'table')
		
		# Statistics
		queryset = EquipmentTag.objects.all()
		if self.request.GET.get('project'):
			queryset = queryset.filter(project_id=self.request.GET['project'])
		
		context['total_count'] = queryset.count()
		context['installed_count'] = queryset.filter(status='INST').count()
		context['delivered_count'] = queryset.filter(status='DLVD').count()
		context['commissioned_count'] = queryset.filter(status='COMM').count()
		context['defective_count'] = queryset.filter(status='DEF').count()
		
		# Status distribution for charts
		status_distribution = queryset.values('status').annotate(
				count=Count('id')
				).order_by('status')
		context['status_distribution'] = status_distribution
		
		# Equipment type distribution
		type_distribution = queryset.values('equipment_type').annotate(
				count=Count('id')
				).order_by('-count')[:10]
		context['type_distribution'] = type_distribution
		
		# Recent tags
		context['recent_tags'] = queryset.order_by('-created_at')[:5]
		
		# Projects for filter dropdown
		context['projects'] = Project.objects.all()
		
		# Bulk action tag IDs (for checkboxes)
		if self.request.GET.getlist('selected_tags'):
			context['selected_tag_ids'] = self.request.GET.getlist('selected_tags')
		
		return context



class EquipmentTagDetailView( generic.DetailView):
	model = EquipmentTag
	template_name = 'core/equipment_tag_detail.html'
	context_object_name = 'tag'
	
	def get_queryset(self):
		return EquipmentTag.objects.select_related(
				'project', 'area', 'system', 'parent_tag'
				).prefetch_related(
				'child_tags',
				'tag_documents__document',
				'purchase_orders__purchase_order',
				'work_package_items__work_package',
				'test_procedures',
				'punch_items',
				'installation_checks',
				'locations__images',  # Prefetch locations with images
				'locations__area',
				'locations__recorded_by'
				)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		tag = self.get_object()
		
		# Hierarchy
		context['hierarchy_tree'] = tag.get_hierarchy_tree()
		context['child_tags'] = tag.child_tags.all()
		context['ancestors'] = self.get_ancestors(tag)
		
		# Documents
		context['documents'] = tag.tag_documents.select_related('document').all()
		
		# Purchase Orders
		context['purchase_orders'] = tag.purchase_orders.select_related(
				'purchase_order__supplier'
				).all()
		
		# Work Packages
		context['work_package_items'] = tag.work_package_items.select_related(
				'work_package__area'
				).all()
		
		# Test Procedures
		context['test_procedures'] = tag.test_procedures.select_related(
				'commissioning_system__system'
				).prefetch_related('test_records').all()
		
		# Punch Items
		context['punch_items'] = tag.punch_items.select_related(
				'raised_by', 'assigned_to'
				).all()
		context['open_punch_count'] = tag.punch_items.filter(
				status__in=['OPEN', 'IPRO']
				).count()
		
		# Installation Checks
		context['installation_checks'] = tag.installation_checks.select_related(
				'checked_by'
				).prefetch_related('photos').all()
		
		# Locations
		context['locations'] = tag.locations.select_related(
				'area', 'recorded_by', 'verified_by'
				).prefetch_related('images').order_by('-arrival_date')
		context['current_location'] = tag.current_location
		context['location_history'] = tag.locations.filter(
				is_current=False
				).order_by('-arrival_date')
		context['total_locations'] = tag.locations.count()
		context['verified_locations'] = tag.locations.filter(is_verified=True).count()
		
		# Related tags
		context['related_tags'] = EquipmentTag.objects.filter(
				Q(area=tag.area) | Q(system=tag.system),
				project=tag.project
				).exclude(pk=tag.pk)[:10]
		
		# Recent activity
		context['recent_activities'] = self.get_recent_activities(tag)
		
		# Quick stats
		context['total_documents'] = tag.tag_documents.count()
		context['total_children'] = tag.child_tags.count()
		context['total_punch_items'] = tag.punch_items.count()
		context['total_test_procedures'] = tag.test_procedures.count()
		
		return context
	
	def get_ancestors(self, tag):
		"""Get all ancestors of a tag."""
		ancestors = []
		current = tag.parent_tag
		while current:
			ancestors.append(current)
			current = current.parent_tag
		return list(reversed(ancestors))
	
	def get_recent_activities(self, tag):
		"""Get recent activities related to this tag."""
		activities = []
		
		# Recent installation checks
		for check in tag.installation_checks.order_by('-checked_date')[:3]:
			activities.append({
					'icon': 'check-circle',
					'description': f'Installation check performed - {check.get_status_display()}',
					'date': check.checked_date,
					'user': check.checked_by.get_full_name() if check.checked_by else 'System',
					'type': 'installation'
					})
		
		# Recent location updates
		for location in tag.locations.order_by('-arrival_date')[:3]:
			activities.append({
					'icon': 'geo-alt',
					'description': f'Location recorded - {location.get_location_type_display()} ({location.latitude}, {location.longitude})',
					'date': location.arrival_date.date(),
					'user': location.recorded_by.get_full_name() if location.recorded_by else 'System',
					'type': 'location'
					})
		
		# Recent test records
		try:
			from commissioning.models import TestRecord
			recent_tests = TestRecord.objects.filter(
					test_procedure__equipment_tags=tag
					).order_by('-start_datetime')[:3]
			for test in recent_tests:
				activities.append({
						'icon': 'clipboard-check',
						'description': f'Test "{test.test_procedure.code}" - {test.get_result_display()}',
						'date': test.start_datetime.date(),
						'user': test.executed_by.get_full_name() if test.executed_by else 'System',
						'type': 'test'
						})
		except:
			pass
		
		# Recent punch items
		for punch in tag.punch_items.order_by('-raised_date')[:3]:
			activities.append({
					'icon': 'flag',
					'description': f'Punch item {punch.punch_number} - {punch.get_status_display()}',
					'date': punch.raised_date,
					'user': punch.raised_by.get_full_name() if punch.raised_by else 'System',
					'type': 'punch'
					})
		
		# Sort by date
		activities.sort(key=lambda x: x['date'], reverse=True)
		return activities[:10]
	
	
	
class EquipmentTagDetailView2(LoginRequiredMixin, generic.DetailView):
	model = EquipmentTag
	template_name = 'core/equipment_tag_detail.html'
	context_object_name = 'tag'
	
	def get_queryset(self):
		return EquipmentTag.objects.select_related(
				'project', 'area', 'system', 'parent_tag'
				).prefetch_related(
				'child_tags',
				'tag_documents__document',
				'purchase_orders__purchase_order',
				'work_package_items__work_package',
				'test_procedures',
				'punch_items',
				'installation_checks'
				)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		tag = self.get_object()
		
		# Hierarchy
		context['hierarchy_tree'] = tag.get_hierarchy_tree()
		context['child_tags'] = tag.child_tags.all()
		context['ancestors'] = self.get_ancestors(tag)
		
		# Documents
		context['documents'] = tag.tag_documents.select_related('document').all()
		
		# Purchase Orders
		context['purchase_orders'] = tag.purchase_orders.select_related(
				'purchase_order__supplier'
				).all()
		
		# Work Packages
		context['work_package_items'] = tag.work_package_items.select_related(
				'work_package__area'
				).all()
		
		# Test Procedures
		context['test_procedures'] = tag.test_procedures.select_related(
				'commissioning_system__system'
				).prefetch_related('test_records').all()
		
		# Punch Items
		context['punch_items'] = tag.punch_items.select_related(
				'raised_by', 'assigned_to'
				).all()
		context['open_punch_count'] = tag.punch_items.filter(
				status__in=['OPEN', 'IPRO']
				).count()
		
		# Installation Checks
		context['installation_checks'] = tag.installation_checks.select_related(
				'checked_by'
				).prefetch_related('photos').all()
		
		# Related tags (same area or system)
		context['related_tags'] = EquipmentTag.objects.filter(
				Q(area=tag.area) | Q(system=tag.system),
				project=tag.project
				).exclude(pk=tag.pk)[:10]
		
		# Status history (if you implement tracking)
		context['status_history'] = self.get_status_history(tag)
		
		# Recent activity
		context['recent_activities'] = self.get_recent_activities(tag)
		
		# Quick stats
		context['total_documents'] = tag.tag_documents.count()
		context['total_children'] = tag.child_tags.count()
		context['total_punch_items'] = tag.punch_items.count()
		context['total_test_procedures'] = tag.test_procedures.count()
		
		return context
	
	def get_ancestors(self, tag):
		"""Get all ancestors of a tag."""
		ancestors = []
		current = tag.parent_tag
		while current:
			ancestors.append(current)
			current = current.parent_tag
		return list(reversed(ancestors))
	
	def get_status_history(self, tag):
		"""Get status change history if tracking is implemented."""
		# This is a placeholder - implement based on your tracking mechanism
		return []
	
	def get_recent_activities(self, tag):
		"""Get recent activities related to this tag."""
		activities = []
		
		# Recent installation checks
		for check in tag.installation_checks.order_by('-checked_date')[:3]:
			activities.append(
					{
							'icon':        'check-circle',
							'description': f'Installation check performed - {check.get_status_display()}',
							'date':        check.checked_date,
							'user':        check.checked_by.get_full_name() if check.checked_by else 'System'
							}
					)
		
		# Recent test records
		from commissioning.models import TestRecord
		recent_tests = TestRecord.objects.filter(
				test_procedure__equipment_tags=tag
				).order_by('-start_datetime')[:3]
		for test in recent_tests:
			activities.append(
					{
							'icon':        'clipboard-check',
							'description': f'Test "{test.test_procedure.code}" - {test.get_result_display()}',
							'date':        test.start_datetime.date(),
							'user':        test.executed_by.get_full_name() if test.executed_by else 'System'
							}
					)
		
		# Recent punch items
		for punch in tag.punch_items.order_by('-raised_date')[:3]:
			activities.append(
					{
							'icon':        'flag',
							'description': f'Punch item {punch.punch_number} - {punch.get_status_display()}',
							'date':        punch.raised_date,
							'user':        punch.raised_by.get_full_name() if punch.raised_by else 'System'
							}
					)
		
		# Sort by date
		activities.sort(key=lambda x: x['date'], reverse=True)
		return activities[:10]


class DashboardView(LoginRequiredMixin, generic.TemplateView):
	template_name = 'core/dashboard.html'
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		# Project statistics
		context['total_projects'] = Project.objects.count()
		context['active_projects'] = Project.objects.filter(
				status__in=['EXEC', 'COMM']
				).count()
		context['completed_projects'] = Project.objects.filter(
				status='CLSD'
				).count()
		
		# Equipment statistics
		context['total_equipment_tags'] = EquipmentTag.objects.count()
		context['installed_tags'] = EquipmentTag.objects.filter(
				status='INST'
				).count()
		context['commissioned_tags'] = EquipmentTag.objects.filter(
				status='COMM'
				).count()
		
		# Document statistics
		context['total_documents'] = Document.objects.count()
		context['approved_documents'] = Document.objects.filter(
				status='APPR'
				).count()
		
		# Punch items
		context['open_punch_items'] = PunchItem.objects.filter(
				status__in=['OPEN', 'IPRO']
				).count()
		context['critical_punch_items'] = PunchItem.objects.filter(
				status__in=['OPEN', 'IPRO'],
				category='A'
				).count()
		
		# Work packages
		context['active_work_packages'] = WorkPackage.objects.filter(
				status='IPRO'
				).count()
		context['completed_work_packages'] = WorkPackage.objects.filter(
				status='COMP'
				).count()
		
		# Recent projects
		context['recent_projects'] = Project.objects.order_by('-created_at')[:5]
		
		# Recent equipment tags
		context['recent_tags'] = EquipmentTag.objects.select_related(
				'project', 'area'
				).order_by('-created_at')[:10]
		
		# Overdue work packages
		context['overdue_work_packages'] = WorkPackage.objects.filter(
				status__in=['IPRO', 'NSTA'],
				planned_finish__lt=timezone.now().date()
				).select_related('project', 'area').order_by('planned_finish')[:5]
		
		# Recent documents
		context['recent_documents'] = Document.objects.select_related(
				'project'
				).order_by('-created_at')[:5]
		
		# Recent punch items
		context['recent_punch_items'] = PunchItem.objects.filter(
				status__in=['OPEN', 'IPRO']
				).select_related(
				'project', 'equipment_tag', 'raised_by'
				).order_by('-raised_date')[:5]
		
		# Projects overview for cards
		context['projects_overview'] = Project.objects.annotate(
				equipment_count=Count('equipment_tags', distinct=True),
				document_count=Count('documents', distinct=True),
				work_package_count=Count('work_packages', distinct=True),
				punch_item_count=Count('punch_items', distinct=True),
				open_punch_count=Count(
						'punch_items',
						filter=Q(punch_items__status__in=['OPEN', 'IPRO']),
						distinct=True
						)
				).order_by('-created_at')
		
		return context



class EquipmentLocationCreateView(LoginRequiredMixin, generic.CreateView):
	"""Record a new location for equipment."""
	model = EquipmentLocation
	form_class = EquipmentLocationForm
	template_name = 'core/equipment_location_form.html'
	
	def get_success_url(self):
		return self.object.equipment_tag.get_absolute_url()
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		tag_id = self.kwargs.get('tag_id') or self.request.GET.get('tag')
		if tag_id:
			kwargs['tag_id'] = tag_id
		return kwargs
	
	def get_initial(self):
		initial = super().get_initial()
		initial['arrival_date'] = timezone.now()
		initial['is_current'] = True
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		tag_id = self.kwargs.get('tag_id') or self.request.GET.get('tag')
		if tag_id:
			context['equipment_tag'] = get_object_or_404(EquipmentTag, pk=tag_id)
		return context
	
	def form_valid(self, form):
		form.instance.recorded_by = self.request.user
		messages.success(self.request, 'Equipment location recorded successfully.')
		return super().form_valid(form)


class EquipmentLocationDetailView(LoginRequiredMixin, generic.DetailView):
	"""View location details with images."""
	model = EquipmentLocation
	template_name = 'core/equipment_location_detail.html'
	context_object_name = 'location'
	
	def get_queryset(self):
		return EquipmentLocation.objects.select_related(
				'equipment_tag', 'area', 'recorded_by', 'verified_by'
				).prefetch_related('images')
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['image_form'] = EquipmentLocationImageForm()
		context['google_maps_url'] = self.object.google_maps_url
		context['openstreetmap_url'] = self.object.openstreetmap_url
		return context


@login_required
def upload_location_image(request, location_id):
	"""Upload an image for a location."""
	location = get_object_or_404(EquipmentLocation, pk=location_id)
	
	if request.method == 'POST':
		form = EquipmentLocationImageForm(request.POST, request.FILES)
		if form.is_valid():
			image = form.save(commit=False)
			image.location = location
			image.uploaded_by = request.user
			image.save()
			messages.success(request, 'Image uploaded successfully.')
		else:
			messages.error(request, 'Please correct the errors below.')
	
	return redirect('core:equipment_location_detail', pk=location.pk)


@login_required
def delete_location_image(request, image_id):
	"""Delete a location image."""
	image = get_object_or_404(EquipmentLocationImage, pk=image_id)
	location_id = image.location_id
	
	if request.method == 'POST':
		image.delete()
		messages.success(request, 'Image deleted successfully.')
	
	return redirect('core:equipment_location_detail', pk=location_id)


@login_required
def set_primary_image(request, image_id):
	"""Set an image as primary for its location."""
	image = get_object_or_404(EquipmentLocationImage, pk=image_id)
	image.is_primary = True
	image.save()
	messages.success(request, 'Primary image updated.')
	return redirect('core:equipment_location_detail', pk=image.location_id)


@login_required
def verify_location(request, location_id):
	"""Verify a location."""
	location = get_object_or_404(EquipmentLocation, pk=location_id)
	
	if request.method == 'POST':
		location.is_verified = True
		location.verified_by = request.user
		location.verified_date = timezone.now()
		location.save()
		messages.success(request, 'Location verified successfully.')
	
	return redirect('core:equipment_location_detail', pk=location.pk)


class AreaListView(LoginRequiredMixin, generic.ListView):
	model = Area
	template_name = 'core/area_list.html'
	context_object_name = 'areas'
	paginate_by = 20
	
	def get_queryset(self):
		queryset = Area.objects.select_related('project').annotate(
				equipment_count=Count('equipment_tags', distinct=True),
				work_package_count=Count('work_packages', distinct=True),
				installed_count=Count(
						'equipment_tags',
						filter=Q(equipment_tags__status='INST'),
						distinct=True
						),
				commissioned_count=Count(
						'equipment_tags',
						filter=Q(equipment_tags__status='COMM'),
						distinct=True
						),
				location_count=Count('equipment_locations', distinct=True)
				)
		
		# Apply filters
		project_id = self.request.GET.get('project')
		if project_id:
			queryset = queryset.filter(project_id=project_id)
		
		search = self.request.GET.get('search')
		if search:
			queryset = queryset.filter(
					Q(code__icontains=search) |
					Q(name__icontains=search) |
					Q(description__icontains=search)
					)
		
		has_equipment = self.request.GET.get('has_equipment')
		if has_equipment == 'true':
			queryset = queryset.filter(equipment_count__gt=0)
		elif has_equipment == 'false':
			queryset = queryset.filter(equipment_count=0)
		
		# Apply sorting
		sort = self.request.GET.get('sort', 'code')
		allowed_sorts = [
				'code', '-code',
				'name', '-name',
				'project__name', '-project__name',
				'equipment_count', '-equipment_count',
				'work_package_count', '-work_package_count',
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
		
		# View mode
		context['view_mode'] = self.request.GET.get('view', 'table')
		
		# Statistics
		base_queryset = Area.objects.all()
		project_id = self.request.GET.get('project')
		if project_id:
			base_queryset = base_queryset.filter(project_id=project_id)
		
		context['total_areas'] = base_queryset.count()
		context['total_equipment'] = EquipmentTag.objects.filter(
				area__in=base_queryset
				).count()
		context['total_installed'] = EquipmentTag.objects.filter(
				area__in=base_queryset,
				status='INST'
				).count()
		context['total_work_packages'] = WorkPackage.objects.filter(
				area__in=base_queryset
				).count()
		
		# Projects for filter dropdown
		context['projects'] = Project.objects.all().order_by('code')
		
		# Selected project
		if project_id:
			context['selected_project'] = Project.objects.filter(pk=project_id).first()
		
		return context


class AreaDetailView(LoginRequiredMixin, generic.DetailView):
	model = Area
	template_name = 'core/area_detail.html'
	context_object_name = 'area'
	
	def get_queryset(self):
		return Area.objects.select_related('project')
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		area = self.get_object()
		
		# Equipment Tags
		equipment_tags = EquipmentTag.objects.filter(area=area).select_related(
				'system', 'parent_tag'
				).prefetch_related(
				'tag_documents', 'child_tags'
				).annotate(
				child_count=Count('child_tags', distinct=True),
				document_count=Count('tag_documents', distinct=True)
				).order_by('tag_number')
		
		context['equipment_tags'] = equipment_tags
		context['total_equipment'] = equipment_tags.count()
		
		# Equipment statistics
		equipment_stats = equipment_tags.aggregate(
				installed=Count('pk', filter=Q(status='INST')),
				delivered=Count('pk', filter=Q(status='DLVD')),
				commissioned=Count('pk', filter=Q(status='COMM')),
				defective=Count('pk', filter=Q(status='DEF')),
				engineering=Count('pk', filter=Q(status='ENG')),
				)
		context['equipment_stats'] = equipment_stats
		
		# Equipment by type
		context['equipment_by_type'] = equipment_tags.values(
				'equipment_type'
				).annotate(
				count=Count('id')
				).order_by('-count')
		
		# Equipment by status
		context['equipment_by_status'] = equipment_tags.values(
				'status'
				).annotate(
				count=Count('id')
				).order_by('status')
		
		# Installation progress
		if context['total_equipment'] > 0:
			context['installation_progress'] = int(
					(equipment_stats['installed'] / context['total_equipment']) * 100
					)
		else:
			context['installation_progress'] = 0
		
		# Work Packages
		work_packages = WorkPackage.objects.filter(area=area).select_related(
				'project', 'supervisor'
				).prefetch_related(
				'items'
				).annotate(
				item_count=Count('items', distinct=True),
				completed_items=Count('items', filter=Q(items__is_complete=True), distinct=True),
				report_count=Count('daily_reports', distinct=True),
				total_hours=Sum('timesheets__hours_worked'),
				total_overtime=Sum('timesheets__overtime_hours')
				).order_by('-created_at')
		
		context['work_packages'] = work_packages
		context['total_work_packages'] = work_packages.count()
		
		# Work package statistics
		wp_stats = work_packages.aggregate(
				in_progress=Count('pk', filter=Q(status='IPRO')),
				completed=Count('pk', filter=Q(status='COMP')),
				not_started=Count('pk', filter=Q(status='NSTA')),
				on_hold=Count('pk', filter=Q(status='HOLD')),
				total_hours=Sum('timesheets__hours_worked'),
				total_overtime=Sum('timesheets__overtime_hours')
				)
		context['wp_stats'] = wp_stats
		
		# Timesheets for work packages in this area
		timesheets = Timesheet.objects.filter(
				work_package__area=area
				).select_related(
				'employee', 'work_package', 'approved_by'
				).order_by('-date')[:50]
		
		context['timesheets'] = timesheets
		context['total_timesheets'] = Timesheet.objects.filter(
				work_package__area=area
				).count()
		
		# Timesheet statistics
		timesheet_stats = Timesheet.objects.filter(work_package__area=area).aggregate(
				total_hours=Sum('hours_worked'),
				total_overtime=Sum('overtime_hours'),
				total_entries=Count('id'),
				total_employees=Count('employee', distinct=True)
				)
		context['timesheet_stats'] = timesheet_stats
		
		# This week's hours
		today = timezone.now().date()
		week_start = today - timedelta(days=today.weekday())
		week_timesheets = Timesheet.objects.filter(
				work_package__area=area,
				date__gte=week_start
				)
		context['week_hours'] = week_timesheets.aggregate(
				total=Sum('hours_worked')
				)['total'] or 0
		# Daily reports - Get base queryset first, then slice for display
		daily_reports_base = DailyProgressReport.objects.filter(
				work_package__area=area
				).select_related(
				'work_package', 'reported_by'
				).order_by('-report_date')
		context['total_daily_reports'] = daily_reports_base.count()
	
		# Daily reports
		daily_reports = DailyProgressReport.objects.filter(
				work_package__area=area
				).select_related(
				'work_package', 'reported_by'
				).order_by('-report_date')[:20]
		
		context['daily_reports'] = daily_reports
		# Recent reports (last 7 days)
		seven_days_ago = timezone.now().date() - timedelta(days=7)
		context['recent_reports'] = daily_reports_base.filter(
				report_date__gte=seven_days_ago
				)
		context['recent_reports_count'] = context['recent_reports'].count()
		
		# Reports with issues in last 7 days
		context['reports_with_issues'] = daily_reports_base.filter(
				report_date__gte=seven_days_ago
				).exclude(issues_encountered='').count()


		# Systems in this area
		context['systems'] = System.objects.filter(
				equipment_tags__area=area
				).distinct().annotate(
				equipment_count=Count('equipment_tags', filter=Q(equipment_tags__area=area))
				).order_by('code')
		
		# Equipment Locations
		locations = EquipmentLocation.objects.filter(
				area=area
				).select_related(
				'equipment_tag', 'recorded_by'
				).prefetch_related('images').order_by('-arrival_date')[:20]
		
		context['locations'] = locations
		context['total_locations'] = EquipmentLocation.objects.filter(area=area).count()
		
		# Current locations (most recent per equipment)
		context['current_locations'] = EquipmentLocation.objects.filter(
				area=area,
				is_current=True
				).select_related('equipment_tag').order_by('equipment_tag__tag_number')
		
		# Punch Items
		punch_items = PunchItem.objects.filter(
				Q(equipment_tag__area=area) | Q(system__equipment_tags__area=area)
				).distinct().select_related(
				'equipment_tag', 'raised_by', 'assigned_to'
				).order_by('-raised_date')
		
		context['punch_items'] = punch_items
		context['total_punch_items'] = punch_items.count()
		context['open_punch_items'] = punch_items.filter(
				status__in=['OPEN', 'IPRO']
				).count()
		context['critical_punch_items'] = punch_items.filter(
				status__in=['OPEN', 'IPRO'],
				category='A'
				).count()
		
		# Recent activities
		context['activities'] = self.get_area_activities(area)
		
		# Today's date
		context['today'] = today
		
		return context

	def get_area_activities(self, area):
		"""Get recent activities for this area."""
		from datetime import datetime, date, time
		from django.utils import timezone as django_timezone
		
		def to_aware_datetime(d):
			"""Convert any date/datetime to timezone-aware datetime."""
			if d is None:
				return django_timezone.make_aware(
						datetime.min,
						django_timezone.get_current_timezone()
						)
			
			if isinstance(d, datetime):
				if django_timezone.is_aware(d):
					return d
				return django_timezone.make_aware(d, django_timezone.get_current_timezone())
			
			if isinstance(d, date):
				naive_dt = datetime.combine(d, time.min)
				return django_timezone.make_aware(naive_dt, django_timezone.get_current_timezone())
			
			return django_timezone.make_aware(
					datetime.min,
					django_timezone.get_current_timezone()
					)
		
		activities = []
		
		# Recent equipment updates
		for tag in EquipmentTag.objects.filter(area=area).order_by('-updated_at')[:5]:
			activities.append({
					'icon': 'tag',
					'description': f'Equipment {tag.tag_number} updated - Status: {tag.get_status_display()}',
					'date': to_aware_datetime(tag.updated_at),
					'type': 'equipment'
					})
		
		# Recent daily reports
		for report in DailyProgressReport.objects.filter(
				work_package__area=area
				).select_related('work_package', 'reported_by').order_by('-created_at')[:5]:
			activities.append({
					'icon': 'journal-text',
					'description': f'Daily report for {report.work_package.code} on {report.report_date}',
					'date': to_aware_datetime(report.created_at),
					'type': 'report'
					})
		
		# Recent timesheets
		for ts in Timesheet.objects.filter(
				work_package__area=area
				).select_related('employee', 'work_package').order_by('-date', '-id')[:5]:
			activities.append({
					'icon': 'clock',
					'description': f'{ts.employee.full_name} logged {ts.hours_worked}h on {ts.work_package.code}',
					'date': to_aware_datetime(ts.date),
					'type': 'timesheet'
					})
		
		# Recent locations
		for loc in EquipmentLocation.objects.filter(
				area=area
				).select_related('equipment_tag').order_by('-created_at')[:5]:
			activities.append({
					'icon': 'geo-alt',
					'description': f'Location recorded for {loc.equipment_tag.tag_number}',
					'date': to_aware_datetime(loc.created_at),
					'type': 'location'
					})
		
		# Recent punch items
		for punch in PunchItem.objects.filter(
				Q(equipment_tag__area=area) | Q(system__equipment_tags__area=area)
				).distinct().order_by('-raised_date')[:5]:
			activities.append({
					'icon': 'flag',
					'description': f'Punch item {punch.punch_number} - {punch.get_status_display()}',
					'date': to_aware_datetime(punch.raised_date),
					'type': 'punch'
					})
		
		# Sort by date - all dates are now timezone-aware datetime objects
		activities.sort(key=lambda x: x['date'], reverse=True)
		return activities[:15]


class SystemListView(LoginRequiredMixin, generic.ListView):
	model = System
	template_name = 'core/system_list.html'
	context_object_name = 'systems'
	paginate_by = 20
	
	def get_queryset(self):
		queryset = System.objects.select_related('project').prefetch_related(
				'equipment_tags',
				'commissioning_phases'
				).annotate(
				equipment_count=Count('equipment_tags', distinct=True),
				installed_count=Count(
						Case(
								When(equipment_tags__status='INST', then=1),
								output_field=CharField(),
								),
						distinct=True
						),
				commissioned_count=Count(
						Case(
								When(equipment_tags__status='COMM', then=1),
								output_field=CharField(),
								),
						distinct=True
						),
				defective_count=Count(
						Case(
								When(equipment_tags__status='DEF', then=1),
								output_field=CharField(),
								),
						distinct=True
						),
				work_package_count=Count('work_packages', distinct=True),
				punch_item_count=Count('punch_items', distinct=True),
				open_punch_count=Count(
						Case(
								When(punch_items__status__in=['OPEN', 'IPRO'], then=1),
								output_field=CharField(),
								),
						distinct=True
						)
				)
		
		# Apply filters
		form = SystemSearchForm(self.request.GET)
		if form.is_valid():
			data = form.cleaned_data
			
			if data.get('project'):
				queryset = queryset.filter(project=data['project'])
			
			if data.get('search'):
				search = data['search']
				queryset = queryset.filter(
						Q(code__icontains=search) |
						Q(name__icontains=search) |
						Q(description__icontains=search)
						)
			
			if data.get('has_commissioning') == 'true':
				queryset = queryset.filter(commissioning_phases__isnull=False)
			
			if data.get('commissioning_status'):
				queryset = queryset.filter(
						commissioning_phases__status=data['commissioning_status']
						)
			
			if data.get('has_defects') == 'true':
				queryset = queryset.filter(defective_count__gt=0)
		
		# Apply sorting
		sort = self.request.GET.get('sort', 'code')
		allowed_sorts = [
				'code', '-code',
				'name', '-name',
				'equipment_count', '-equipment_count',
				'installed_count', '-installed_count',
				'commissioned_count', '-commissioned_count',
				'defective_count', '-defective_count',
				'work_package_count', '-work_package_count',
				'open_punch_count', '-open_punch_count',
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
		context['search_form'] = SystemSearchForm(self.request.GET)
		
		# View mode
		context['view_mode'] = self.request.GET.get('view', 'table')
		
		# Statistics
		base_queryset = System.objects.all()
		project_id = self.request.GET.get('project')
		if project_id:
			base_queryset = base_queryset.filter(project_id=project_id)
		
		context['total_systems'] = base_queryset.count()
		context['total_equipment'] = EquipmentTag.objects.filter(
				system__in=base_queryset
				).count()
		context['total_installed'] = EquipmentTag.objects.filter(
				system__in=base_queryset,
				status='INST'
				).count()
		context['total_commissioned'] = EquipmentTag.objects.filter(
				system__in=base_queryset,
				status='COMM'
				).count()
		
		# Systems with commissioning
		context['systems_in_commissioning'] = base_queryset.filter(
				commissioning_phases__isnull=False
				).distinct().count()
		
		# Systems with defects
		context['systems_with_defects'] = base_queryset.annotate(
				def_count=Count('equipment_tags', filter=Q(equipment_tags__status='DEF'))
				).filter(def_count__gt=0).count()
		
		# Projects for filter
		context['projects'] = Project.objects.all()
		
		# Commissioning status distribution
		try:
			from ..models.commissioning import CommissioningSystem
			context['commissioning_status_distribution'] = CommissioningSystem.objects.filter(
					system__in=base_queryset
					).values('status').annotate(count=Count('id')).order_by('status')
		except:
			context['commissioning_status_distribution'] = []
		
		# Equipment type distribution within systems
		context['equipment_type_distribution'] = EquipmentTag.objects.filter(
				system__in=base_queryset
				).values('equipment_type').annotate(count=Count('id')).order_by('-count')
		
		return context
	
