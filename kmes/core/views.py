from datetime import timezone

from django.db.models import Q, Count, Case, When, Value, CharField
from django.http import HttpResponse
# views.py
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from django.views import generic
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Project, Area, System, EquipmentTag
from .forms import ProjectForm, AreaForm, SystemForm, EquipmentTagForm, EquipmentTagFilterForm
from construction.models import WorkPackage
from commissioning.models import PunchItem
from documents.models import Document
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
class ProjectCreateView(CreateView):
	model = Project
	form_class = ProjectForm
	template_name = "core/project_form.html"
	success_url = reverse_lazy("core:project-list")  # adjust to your list view name


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


class SystemCreateView(LoginRequiredMixin, CreateView):
	model = System
	form_class = SystemForm
	template_name = "core/system_form.html"
	
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
	
	def form_valid(self, form):
		if self.project:
			form.instance.project = self.project
		return super().form_valid(form)
	
	def get_success_url(self):
		return reverse("core:project-detail", kwargs={"pk": self.object.project.pk})


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


class EquipmentTagDetailView(LoginRequiredMixin, generic.DetailView):
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