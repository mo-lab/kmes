from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db import models as db_models

from ..core.models import Project, Area, System, EquipmentTag
from ..core.forms import (
	ProjectForm, AreaForm, SystemForm, EquipmentTagForm,
	EquipmentTagFilterForm, EquipmentTagBulkUpdateForm,
	EquipmentTagHierarchyMoveForm
	)
from ..base_views import BaseCreateView, BaseUpdateView, BaseDeleteView


# ============================================
# PROJECT VIEWS
# ============================================

class ProjectListView(LoginRequiredMixin, generic.ListView):
	model = Project
	template_name = 'core/project_list.html'
	context_object_name = 'projects'
	paginate_by = 20
	ordering = ['-created_at']


class ProjectDetailView(LoginRequiredMixin, generic.DetailView):
	model = Project
	template_name = 'core/project_detail.html'
	context_object_name = 'project'
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		project = self.get_object()
		context['areas'] = project.areas.all()
		context['systems'] = project.systems.all()
		context['equipment_count'] = project.equipment_tags.count()
		return context


class ProjectCreateView(BaseCreateView):
	model = Project
	form_class = ProjectForm
	template_name = 'core/project_form.html'
	success_message = "Project '%(name)s' was created successfully."
	
	def get_success_url(self):
		return reverse('project_detail', kwargs={'pk': self.object.pk})


class ProjectUpdateView(BaseUpdateView):
	model = Project
	form_class = ProjectForm
	template_name = 'core/project_form.html'
	success_message = "Project '%(name)s' was updated successfully."
	
	def get_success_url(self):
		return reverse('project_detail', kwargs={'pk': self.object.pk})


class ProjectDeleteView(BaseDeleteView):
	model = Project
	template_name = 'core/project_confirm_delete.html'
	success_url = reverse_lazy('project_list')
	success_message = "Project was deleted successfully."


# ============================================
# AREA VIEWS
# ============================================

class AreaListView(LoginRequiredMixin, generic.ListView):
	model = Area
	template_name = 'core/area_list.html'
	context_object_name = 'areas'
	
	def get_queryset(self):
		queryset = Area.objects.all()
		project_id = self.request.GET.get('project')
		if project_id:
			queryset = queryset.filter(project_id=project_id)
		return queryset
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['projects'] = Project.objects.all()
		return context


class AreaCreateView(BaseCreateView):
	model = Area
	form_class = AreaForm
	template_name = 'core/area_form.html'
	success_message = "Area '%(code)s - %(name)s' was created successfully."
	
	def get_success_url(self):
		return reverse('area_list')
	
	def get_initial(self):
		initial = super().get_initial()
		project_id = self.kwargs.get('project_id')
		if project_id:
			initial['project'] = get_object_or_404(Project, pk=project_id)
		return initial


class AreaUpdateView(BaseUpdateView):
	model = Area
	form_class = AreaForm
	template_name = 'core/area_form.html'
	success_message = "Area '%(code)s - %(name)s' was updated successfully."
	
	def get_success_url(self):
		return reverse('area_list')


class AreaDeleteView(BaseDeleteView):
	model = Area
	template_name = 'core/area_confirm_delete.html'
	success_url = reverse_lazy('area_list')
	success_message = "Area was deleted successfully."


# ============================================
# SYSTEM VIEWS
# ============================================

class SystemListView(LoginRequiredMixin, generic.ListView):
	model = System
	template_name = 'core/system_list.html'
	context_object_name = 'systems'
	
	def get_queryset(self):
		queryset = System.objects.all()
		project_id = self.request.GET.get('project')
		if project_id:
			queryset = queryset.filter(project_id=project_id)
		return queryset
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['projects'] = Project.objects.all()
		return context


class SystemCreateView(BaseCreateView):
	model = System
	form_class = SystemForm
	template_name = 'core/system_form.html'
	success_message = "System '%(code)s - %(name)s' was created successfully."
	
	def get_success_url(self):
		return reverse('system_list')
	
	def get_initial(self):
		initial = super().get_initial()
		project_id = self.kwargs.get('project_id')
		if project_id:
			initial['project'] = get_object_or_404(Project, pk=project_id)
		return initial


class SystemUpdateView(BaseUpdateView):
	model = System
	form_class = SystemForm
	template_name = 'core/system_form.html'
	success_message = "System '%(code)s - %(name)s' was updated successfully."
	
	def get_success_url(self):
		return reverse('system_list')


class SystemDeleteView(BaseDeleteView):
	model = System
	template_name = 'core/system_confirm_delete.html'
	success_url = reverse_lazy('system_list')
	success_message = "System was deleted successfully."


# ============================================
# EQUIPMENT TAG VIEWS
# ============================================

class EquipmentTagListView(LoginRequiredMixin, generic.ListView):
	model = EquipmentTag
	template_name = 'core/equipment_tag_list.html'
	context_object_name = 'tags'
	paginate_by = 50
	
	def get_queryset(self):
		queryset = EquipmentTag.objects.select_related('project', 'area', 'parent_tag')
		form = EquipmentTagFilterForm(self.request.GET)
		
		if form.is_valid():
			data = form.cleaned_data
			if data.get('project'):
				queryset = queryset.filter(project=data['project'])
			if data.get('area'):
				queryset = queryset.filter(area=data['area'])
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
						db_models.Q(tag_number__icontains=search) |
						db_models.Q(description__icontains=search)
						)
		
		return queryset
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['filter_form'] = EquipmentTagFilterForm(self.request.GET)
		return context


class EquipmentTagDetailView(LoginRequiredMixin, generic.DetailView):
	model = EquipmentTag
	template_name = 'core/equipment_tag_detail.html'
	context_object_name = 'tag'
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		tag = self.get_object()
		context['hierarchy_tree'] = tag.get_hierarchy_tree()
		context['child_tags'] = tag.child_tags.all()
		context['documents'] = tag.tag_documents.select_related('document').all()
		context['purchase_orders'] = tag.purchase_orders.select_related('purchase_order').all()
		context['test_procedures'] = tag.test_procedures.all()
		context['punch_items'] = tag.punch_items.all()
		context['installation_checks'] = tag.installation_checks.all()
		return context


class EquipmentTagCreateView(BaseCreateView):
	model = EquipmentTag
	form_class = EquipmentTagForm
	template_name = 'core/equipment_tag_form.html'
	success_message = "Equipment tag '%(tag_number)s' was created successfully."
	
	def get_success_url(self):
		return reverse('equipment_tag_detail', kwargs={'pk': self.object.pk})
	
	def get_initial(self):
		initial = super().get_initial()
		project_id = self.kwargs.get('project_id')
		if project_id:
			initial['project'] = get_object_or_404(Project, pk=project_id)
		parent_id = self.request.GET.get('parent_tag')
		if parent_id:
			initial['parent_tag'] = get_object_or_404(EquipmentTag, pk=parent_id)
		return initial


class EquipmentTagUpdateView(BaseUpdateView):
	model = EquipmentTag
	form_class = EquipmentTagForm
	template_name = 'core/equipment_tag_form.html'
	success_message = "Equipment tag '%(tag_number)s' was updated successfully."
	
	def get_success_url(self):
		return reverse('equipment_tag_detail', kwargs={'pk': self.object.pk})


class EquipmentTagDeleteView(BaseDeleteView):
	model = EquipmentTag
	template_name = 'core/equipment_tag_confirm_delete.html'
	success_url = reverse_lazy('equipment_tag_list')
	success_message = "Equipment tag was deleted successfully."
	
	def get_success_url(self):
		# Redirect to parent tag or project if available
		tag = self.get_object()
		if tag.parent_tag:
			return reverse('equipment_tag_detail', kwargs={'pk': tag.parent_tag.pk})
		return reverse('project_detail', kwargs={'pk': tag.project_id})


def equipment_tag_hierarchy_view(request, pk):
	"""Display the full hierarchy tree for an equipment tag."""
	tag = get_object_or_404(EquipmentTag, pk=pk)
	move_form = EquipmentTagHierarchyMoveForm(tag=tag)
	
	if request.method == 'POST':
		move_form = EquipmentTagHierarchyMoveForm(request.POST, tag=tag)
		if move_form.is_valid():
			new_parent = move_form.cleaned_data['new_parent_tag']
			tag.parent_tag = new_parent
			tag.save()
			messages.success(request, f"Tag {tag.tag_number} moved successfully.")
			return redirect('equipment_tag_hierarchy', pk=tag.pk)
	
	return render(request, 'core/equipment_tag_hierarchy.html', {
			'tag': tag,
			'hierarchy_tree': tag.get_hierarchy_tree(),
			'move_form': move_form,
			})


def equipment_tag_bulk_update_view(request):
	"""Bulk update equipment tags."""
	if request.method == 'POST':
		form = EquipmentTagBulkUpdateForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			tag_ids = data['tag_ids']
			tags = EquipmentTag.objects.filter(id__in=tag_ids)
			
			updates = {}
			if data.get('status'):
				updates['status'] = data['status']
			if data.get('area'):
				updates['area'] = data['area']
			if data.get('criticality'):
				updates['criticality'] = data['criticality']
			if data.get('installation_date'):
				updates['installation_date'] = data['installation_date']
			
			count = tags.update(**updates)
			messages.success(request, f"Successfully updated {count} equipment tags.")
			return redirect('equipment_tag_list')
	else:
		tag_ids = request.GET.getlist('tags')
		initial = {'tag_ids': ','.join(tag_ids)} if tag_ids else {}
		form = EquipmentTagBulkUpdateForm(initial=initial)
	
	return render(request, 'core/equipment_tag_bulk_update.html', {'form': form})


# ============================================
# AJAX VIEWS FOR DYNAMIC DROPDOWNS
# ============================================

def ajax_load_areas(request):
	"""AJAX endpoint to load areas based on selected project."""
	project_id = request.GET.get('project_id')
	areas = Area.objects.filter(project_id=project_id).values('id', 'code', 'name')
	return JsonResponse(list(areas), safe=False)


def ajax_load_systems(request):
	"""AJAX endpoint to load systems based on selected project."""
	project_id = request.GET.get('project_id')
	systems = System.objects.filter(project_id=project_id).values('id', 'code', 'name')
	return JsonResponse(list(systems), safe=False)


def ajax_load_tags(request):
	"""AJAX endpoint to load equipment tags based on selected project."""
	project_id = request.GET.get('project_id')
	tags = EquipmentTag.objects.filter(project_id=project_id).values('id', 'tag_number', 'description')
	return JsonResponse(list(tags), safe=False)