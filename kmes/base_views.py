from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.db import models


class ProjectContextMixin:
	"""Mixin to add project context for filtering."""
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		if hasattr(self, 'object') and self.object:
			if hasattr(self.object, 'project'):
				context['project'] = self.object.project
			elif hasattr(self.object, 'project_id'):
				from core.models import Project
				context['project'] = Project.objects.get(pk=self.object.project_id)
		return context
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		# Pass project_id to forms for filtering dropdowns
		project_id = self.kwargs.get('project_id')
		if project_id:
			kwargs['project_id'] = project_id
		elif hasattr(self, 'object') and self.object:
			if hasattr(self.object, 'project_id'):
				kwargs['project_id'] = self.object.project_id
		return kwargs


class SuccessUrlMixin:
	"""Mixin to determine success URL dynamically."""
	success_url = None
	
	def get_success_url(self):
		if self.success_url:
			return self.success_url
		return reverse_lazy('dashboard')  # Default fallback


class BaseCreateView(LoginRequiredMixin, SuccessMessageMixin, SuccessUrlMixin, ProjectContextMixin, models.CreateView):
	"""Base create view with common functionality."""
	template_name = None  # Set in child class or use default
	
	def form_valid(self, form):
		# Auto-set created_by/user fields if they exist
		if hasattr(form.instance, 'created_by'):
			form.instance.created_by = self.request.user
		if hasattr(form.instance, 'raised_by') and not form.instance.pk:
			form.instance.raised_by = self.request.user
		if hasattr(form.instance, 'submitted_by') and not form.instance.pk:
			form.instance.submitted_by = self.request.user
		return super().form_valid(form)


class BaseUpdateView(LoginRequiredMixin, SuccessMessageMixin, SuccessUrlMixin, ProjectContextMixin, models.UpdateView):
	"""Base update view with common functionality."""
	
	def form_valid(self, form):
		# Auto-set approved/verified by fields based on status changes
		if hasattr(form.instance, 'status'):
			old_status = type(form.instance).objects.get(pk=form.instance.pk).status
			new_status = form.cleaned_data.get('status')
			
			if hasattr(form.instance, 'approved_by') and 'APPR' in str(new_status):
				form.instance.approved_by = self.request.user
			if hasattr(form.instance, 'verified_by') and 'CLSD' in str(new_status):
				form.instance.verified_by = self.request.user
		return super().form_valid(form)


class BaseDeleteView(LoginRequiredMixin, SuccessMessageMixin, SuccessUrlMixin, models.DeleteView):
	"""Base delete view with common functionality."""
	
	def get_success_message(self, cleaned_data):
		return f"{self.model.__name__} successfully deleted."