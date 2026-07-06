# from django.views import generic
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib import messages
# from django.shortcuts import render, redirect, get_object_or_404
# from django.urls import reverse, reverse_lazy
# from django.http import JsonResponse
#
# from ..construction.models import (
# 	WorkPackage, WorkPackageItem, DailyProgressReport,
# 	InstalledItemCheck, InstallationCheckPhoto
# 	)
# from ..core.models import Project, EquipmentTag
# from ..construction.forms import (
# 	WorkPackageForm, WorkPackageItemForm, DailyProgressReportForm,
# 	InstalledItemCheckForm, InstallationCheckPhotoForm,
# 	WorkPackageProgressUpdateForm
# 	)
# from ..base_views import BaseCreateView, BaseUpdateView, BaseDeleteView
#
#
# # ============================================
# # WORK PACKAGE VIEWS
# # ============================================
#
# class WorkPackageListView(LoginRequiredMixin, generic.ListView):
# 	model = WorkPackage
# 	template_name = 'construction/work_package_list.html'
# 	context_object_name = 'work_packages'
# 	paginate_by = 25
#
# 	def get_queryset(self):
# 		queryset = WorkPackage.objects.select_related('project', 'area', 'supervisor')
# 		project_id = self.request.GET.get('project')
# 		if project_id:
# 			queryset = queryset.filter(project_id=project_id)
# 		status = self.request.GET.get('status')
# 		if status:
# 			queryset = queryset.filter(status=status)
# 		return queryset.order_by('code')
#
#
# class WorkPackageDetailView(LoginRequiredMixin, generic.DetailView):
# 	model = WorkPackage
# 	template_name = 'construction/work_package_detail.html'
# 	context_object_name = 'work_package'
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		wp = self.get_object()
# 		context['items'] = wp.items.select_related('equipment_tag').all()
# 		context['daily_reports'] = wp.daily_reports.order_by('-report_date')[:10]
# 		context['timesheets'] = wp.timesheets.select_related('employee').order_by('-date')[:20]
# 		context['tool_assignments'] = wp.tool_assignments.select_related('tool_plant').all()
# 		context['progress_form'] = WorkPackageProgressUpdateForm(instance=wp)
# 		return context
#
#
# class WorkPackageCreateView(BaseCreateView):
# 	model = WorkPackage
# 	form_class = WorkPackageForm
# 	template_name = 'construction/work_package_form.html'
# 	success_message = "Work Package '%(code)s' was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('work_package_detail', kwargs={'pk': self.object.pk})
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		project_id = self.kwargs.get('project_id')
# 		if project_id:
# 			initial['project'] = get_object_or_404(Project, pk=project_id)
# 		area_id = self.kwargs.get('area_id')
# 		if area_id:
# 			from ..core.models import Area
# 			initial['area'] = get_object_or_404(Area, pk=area_id)
# 		return initial
#
#
# class WorkPackageUpdateView(BaseUpdateView):
# 	model = WorkPackage
# 	form_class = WorkPackageForm
# 	template_name = 'construction/work_package_form.html'
# 	success_message = "Work Package '%(code)s' was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('construction:work_package_detail', kwargs={'pk': self.object.pk})
#
#
# class WorkPackageDeleteView(BaseDeleteView):
# 	model = WorkPackage
# 	template_name = 'construction/work_package_confirm_delete.html'
# 	success_url = reverse_lazy('work_package_list')
# 	success_message = "Work Package was deleted successfully."
#
#
# def work_package_progress_update_view(request, pk):
# 	"""Quick progress update for a work package."""
# 	work_package = get_object_or_404(WorkPackage, pk=pk)
#
# 	if request.method == 'POST':
# 		form = WorkPackageProgressUpdateForm(request.POST, instance=work_package)
# 		if form.is_valid():
# 			form.save()
# 			messages.success(request, "Progress updated successfully.")
# 		else:
# 			messages.error(request, "Please correct the errors below.")
#
# 	return redirect('construction:work_package_detail', pk=work_package.pk)
#
#
# # ============================================
# # WORK PACKAGE ITEM VIEWS
# # ============================================
#
# class WorkPackageItemCreateView(BaseCreateView):
# 	model = WorkPackageItem
# 	form_class = WorkPackageItemForm
# 	template_name = 'construction/work_package_item_form.html'
# 	success_message = "Equipment tag added to work package successfully."
#
# 	def get_success_url(self):
# 		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		work_package_id = self.kwargs.get('work_package_id')
# 		if work_package_id:
# 			work_package = get_object_or_404(WorkPackage, pk=work_package_id)
# 			initial['work_package'] = work_package
# 		return initial
#
# 	def get_form_kwargs(self):
# 		kwargs = super().get_form_kwargs()
# 		work_package_id = self.kwargs.get('work_package_id')
# 		if work_package_id:
# 			work_package = get_object_or_404(WorkPackage, pk=work_package_id)
# 			kwargs['project_id'] = work_package.project_id
# 			kwargs['work_package_id'] = work_package_id
# 		return kwargs
#
#
# class WorkPackageItemDeleteView(BaseDeleteView):
# 	model = WorkPackageItem
# 	template_name = 'construction/work_package_item_confirm_delete.html'
# 	success_message = "Equipment tag removed from work package successfully."
#
# 	def get_success_url(self):
# 		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
#
#
# # ============================================
# # DAILY PROGRESS REPORT VIEWS
# # ============================================
#
# class DailyProgressReportListView(LoginRequiredMixin, generic.ListView):
# 	model = DailyProgressReport
# 	template_name = 'construction/daily_report_list.html'
# 	context_object_name = 'reports'
# 	paginate_by = 25
#
# 	def get_queryset(self):
# 		queryset = DailyProgressReport.objects.select_related('work_package', 'reported_by')
# 		work_package_id = self.request.GET.get('work_package')
# 		if work_package_id:
# 			queryset = queryset.filter(work_package_id=work_package_id)
# 		return queryset.order_by('-report_date')
#
#
# class DailyProgressReportCreateView(BaseCreateView):
# 	model = DailyProgressReport
# 	form_class = DailyProgressReportForm
# 	template_name = 'construction/daily_report_form.html'
# 	success_message = "Daily progress report was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		work_package_id = self.kwargs.get('work_package_id')
# 		if work_package_id:
# 			initial['work_package'] = get_object_or_404(WorkPackage, pk=work_package_id)
# 		return initial
#
#
# class DailyProgressReportUpdateView(BaseUpdateView):
# 	model = DailyProgressReport
# 	form_class = DailyProgressReportForm
# 	template_name = 'construction/daily_report_form.html'
# 	success_message = "Daily progress report was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('work_package_detail', kwargs={'pk': self.object.work_package.pk})
#
#
# class DailyProgressReportDeleteView(BaseDeleteView):
# 	model = DailyProgressReport
# 	template_name = 'construction/daily_report_confirm_delete.html'
# 	success_message = "Daily progress report was deleted successfully."
#
# 	def get_success_url(self):
# 		return reverse('construction:work_package_detail', kwargs={'pk': self.object.work_package.pk})
#
#
# # ============================================
# # INSTALLED ITEM CHECK VIEWS
# # ============================================
#
# class InstalledItemCheckCreateView(BaseCreateView):
# 	model = InstalledItemCheck
# 	form_class = InstalledItemCheckForm
# 	template_name = 'construction/installed_item_check_form.html'
# 	success_message = "Installation check was recorded successfully."
#
# 	def get_success_url(self):
# 		return reverse('equipment_tag_detail', kwargs={'pk': self.object.equipment_tag.pk})
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		tag_id = self.kwargs.get('tag_id')
# 		if tag_id:
# 			initial['equipment_tag'] = get_object_or_404(EquipmentTag, pk=tag_id)
# 		return initial
#
# 	def get_form_kwargs(self):
# 		kwargs = super().get_form_kwargs()
# 		tag_id = self.kwargs.get('tag_id')
# 		if tag_id:
# 			tag = get_object_or_404(EquipmentTag, pk=tag_id)
# 			kwargs['project_id'] = tag.project_id
# 		return kwargs
#
#
# class InstalledItemCheckUpdateView(BaseUpdateView):
# 	model = InstalledItemCheck
# 	form_class = InstalledItemCheckForm
# 	template_name = 'construction/installed_item_check_form.html'
# 	success_message = "Installation check was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('core:equipment_tag_detail', kwargs={'pk': self.object.equipment_tag.pk})
#
#
# class InstalledItemCheckDetailView(LoginRequiredMixin, generic.DetailView):
# 	model = InstalledItemCheck
# 	template_name = 'construction/installed_item_check_detail.html'
# 	context_object_name = 'check'
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		context['photos'] = self.object.photos.all()
# 		context['photo_form'] = InstallationCheckPhotoForm()
# 		return context
#
#
# class InstallationCheckPhotoUploadView(BaseCreateView):
# 	"""Upload photo to an installation check."""
# 	model = InstallationCheckPhoto
# 	form_class = InstallationCheckPhotoForm
# 	template_name = 'construction/installation_check_photo_upload.html'
# 	success_message = "Photo uploaded successfully."
#
# 	def get_success_url(self):
# 		return reverse('installed_item_check_detail', kwargs={'pk': self.kwargs['check_id']})
#
# 	def form_valid(self, form):
# 		check = get_object_or_404(InstalledItemCheck, pk=self.kwargs['check_id'])
# 		form.instance.installation_check = check
# 		return super().form_valid(form)