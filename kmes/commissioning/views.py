# from django.views import generic
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib import messages
# from django.shortcuts import render, redirect, get_object_or_404
# from django.urls import reverse, reverse_lazy
# from django.utils import timezone
#
# from kmes.commissioning.models import (
# 	CommissioningSystem, TestProcedure, TestRecord,
# 	PunchItem, PunchItemPhoto
# 	)
# from kmes.core.models import Project,EquipmentTag
# from kmes.commissioning.forms import (
# 	CommissioningSystemForm, TestProcedureForm, TestRecordForm,
# 	PunchItemForm, PunchItemResolveForm, PunchItemVerifyForm,
# 	PunchItemPhotoForm
# 	)
# from kmes.base_views import BaseCreateView, BaseUpdateView, BaseDeleteView
#
#
# # ============================================
# # COMMISSIONING SYSTEM VIEWS
# # ============================================
#
# class CommissioningSystemListView(LoginRequiredMixin, generic.ListView):
# 	model = CommissioningSystem
# 	template_name = 'commissioning/commissioning_system_list.html'
# 	context_object_name = 'commissioning_systems'
#
# 	def get_queryset(self):
# 		queryset = CommissioningSystem.objects.select_related('system__project')
# 		project_id = self.request.GET.get('project')
# 		if project_id:
# 			queryset = queryset.filter(system__project_id=project_id)
# 		return queryset.order_by('system__code')
#
#
# class CommissioningSystemDetailView(LoginRequiredMixin, generic.DetailView):
# 	model = CommissioningSystem
# 	template_name = 'commissioning/commissioning_system_detail.html'
# 	context_object_name = 'commissioning_system'
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		cs = self.get_object()
# 		context['test_procedures'] = cs.test_procedures.all()
# 		context['punch_items'] = PunchItem.objects.filter(
# 				system=cs.system
# 				).select_related('equipment_tag', 'raised_by')
#
# 		# Calculate progress
# 		total_tests = cs.test_procedures.count()
# 		passed_tests = TestRecord.objects.filter(
# 				test_procedure__commissioning_system=cs,
# 				result='PASS'
# 				).values('test_procedure').distinct().count()
# 		context['progress_percent'] = int((passed_tests / total_tests * 100)) if total_tests > 0 else 0
#
# 		return context
#
#
# class CommissioningSystemCreateView(BaseCreateView):
# 	model = CommissioningSystem
# 	form_class = CommissioningSystemForm
# 	template_name = 'commissioning/commissioning_system_form.html'
# 	success_message = "Commissioning system was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('commissioning:commissioning_system_detail', kwargs={'pk': self.object.pk})
#
#
# class CommissioningSystemUpdateView(BaseUpdateView):
# 	model = CommissioningSystem
# 	form_class = CommissioningSystemForm
# 	template_name = 'commissioning/commissioning_system_form.html'
# 	success_message = "Commissioning system was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('commissioning:commissioning_system_detail', kwargs={'pk': self.object.pk})
#
#
# # ============================================
# # TEST PROCEDURE VIEWS
# # ============================================
#
# class TestProcedureCreateView(BaseCreateView):
# 	model = TestProcedure
# 	form_class = TestProcedureForm
# 	template_name = 'commissioning/test_procedure_form.html'
# 	success_message = "Test procedure '%(code)s' was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('commissioning_system_detail', kwargs={'pk': self.object.commissioning_system.pk})
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		cs_id = self.kwargs.get('commissioning_system_id')
# 		if cs_id:
# 			initial['commissioning_system'] = get_object_or_404(CommissioningSystem, pk=cs_id)
# 		return initial
#
#
# class TestProcedureUpdateView(BaseUpdateView):
# 	model = TestProcedure
# 	form_class = TestProcedureForm
# 	template_name = 'commissioning/test_procedure_form.html'
# 	success_message = "Test procedure '%(code)s' was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('commissioning:commissioning_system_detail', kwargs={'pk': self.object.commissioning_system.pk})
#
#
# class TestProcedureDeleteView(BaseDeleteView):
# 	model = TestProcedure
# 	template_name = 'commissioning/test_procedure_confirm_delete.html'
# 	success_message = "Test procedure was deleted successfully."
#
# 	def get_success_url(self):
# 		return reverse('commissioning:commissioning_system_detail', kwargs={'pk': self.object.commissioning_system.pk})
#
#
# # ============================================
# # TEST RECORD VIEWS
# # ============================================
#
# class TestRecordCreateView(BaseCreateView):
# 	model = TestRecord
# 	form_class = TestRecordForm
# 	template_name = 'commissioning/test_record_form.html'
# 	success_message = "Test record was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('commissioning:test_record_detail', kwargs={'pk': self.object.pk})
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		procedure_id = self.kwargs.get('procedure_id')
# 		if procedure_id:
# 			procedure = get_object_or_404(TestProcedure, pk=procedure_id)
# 			initial['test_procedure'] = procedure
# 			# Auto-increment test number
# 			last_record = procedure.test_records.order_by('-test_number').first()
# 			initial['test_number'] = (last_record.test_number + 1) if last_record else 1
# 		return initial
#
#
# class TestRecordUpdateView(BaseUpdateView):
# 	model = TestRecord
# 	form_class = TestRecordForm
# 	template_name = 'commissioning/test_record_form.html'
# 	success_message = "Test record was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('test_record_detail', kwargs={'pk': self.object.pk})
#
# 	def form_valid(self, form):
# 		if form.cleaned_data.get('result') in ['PASS', 'COND', 'FAIL']:
# 			form.instance.end_datetime = form.instance.end_datetime or timezone.now()
# 		return super().form_valid(form)
#
#
# class TestRecordDetailView(LoginRequiredMixin, generic.DetailView):
# 	model = TestRecord
# 	template_name = 'commissioning/test_record_detail.html'
# 	context_object_name = 'test_record'
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		context['punch_items'] = self.object.punch_items.all()
# 		context['procedure'] = self.object.test_procedure
# 		return context
#
#
# # ============================================
# # PUNCH ITEM VIEWS
# # ============================================
#
# class PunchItemListView(LoginRequiredMixin, generic.ListView):
# 	model = PunchItem
# 	template_name = 'commissioning/punch_item_list.html'
# 	context_object_name = 'punch_items'
# 	paginate_by = 25
#
# 	def get_queryset(self):
# 		queryset = PunchItem.objects.select_related(
# 				'project', 'equipment_tag', 'raised_by', 'assigned_to'
# 				)
#
# 		project_id = self.request.GET.get('project')
# 		if project_id:
# 			queryset = queryset.filter(project_id=project_id)
#
# 		status = self.request.GET.get('status')
# 		if status:
# 			queryset = queryset.filter(status=status)
#
# 		category = self.request.GET.get('category')
# 		if category:
# 			queryset = queryset.filter(category=category)
#
# 		return queryset.order_by('category', '-raised_date')
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		context['projects'] = Project.objects.all()
# 		return context
#
#
# class PunchItemDetailView(LoginRequiredMixin, generic.DetailView):
# 	model = PunchItem
# 	template_name = 'commissioning/punch_item_detail.html'
# 	context_object_name = 'punch_item'
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		punch = self.get_object()
# 		context['photos'] = punch.photos.all()
# 		context['photo_form'] = PunchItemPhotoForm()
#
# 		if punch.status == 'OPEN':
# 			context['resolve_form'] = PunchItemResolveForm(instance=punch)
# 		elif punch.status == 'RESL':
# 			context['verify_form'] = PunchItemVerifyForm(instance=punch)
#
# 		return context
#
#
# class PunchItemCreateView(BaseCreateView):
# 	model = PunchItem
# 	form_class = PunchItemForm
# 	template_name = 'commissioning/punch_item_form.html'
# 	success_message = "Punch item '%(punch_number)s' was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('commissioning:punch_item_detail', kwargs={'pk': self.object.pk})
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		project_id = self.kwargs.get('project_id')
# 		if project_id:
# 			initial['project'] = get_object_or_404(Project, pk=project_id)
# 		tag_id = self.request.GET.get('tag')
# 		if tag_id:
# 			initial['equipment_tag'] = get_object_or_404(EquipmentTag, pk=tag_id)
# 		system_id = self.request.GET.get('system')
# 		if system_id:
# 			from kmes.core.models import System
# 			initial['system'] = get_object_or_404(System, pk=system_id)
# 		return initial
#
# 	def form_valid(self, form):
# 		form.instance.raised_by = self.request.user
# 		form.instance.raised_date = timezone.now().date()
#
# 		# Auto-generate punch number if not provided
# 		if not form.instance.punch_number:
# 			from .models import PunchItem
# 			last_punch = PunchItem.objects.order_by('-id').first()
# 			next_num = (last_punch.id + 1) if last_punch else 1
# 			form.instance.punch_number = f"PUNCH-{timezone.now().year}-{next_num:04d}"
#
# 		return super().form_valid(form)
#
#
# class PunchItemUpdateView(BaseUpdateView):
# 	model = PunchItem
# 	form_class = PunchItemForm
# 	template_name = 'commissioning/punch_item_form.html'
# 	success_message = "Punch item '%(punch_number)s' was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('commissioning:punch_item_detail', kwargs={'pk': self.object.pk})
#
#
# def punch_item_resolve_view(request, pk):
# 	"""Resolve a punch item."""
# 	punch_item = get_object_or_404(PunchItem, pk=pk)
#
# 	if request.method == 'POST':
# 		form = PunchItemResolveForm(request.POST, instance=punch_item)
# 		if form.is_valid():
# 			form.instance.status = 'RESL'
# 			form.instance.resolved_date = form.cleaned_data.get('resolved_date') or timezone.now().date()
# 			form.save()
# 			messages.success(request, f"Punch item {punch_item.punch_number} marked as resolved.")
# 			return redirect('commissioning:punch_item_detail', pk=punch_item.pk)
# 	else:
# 		form = PunchItemResolveForm(instance=punch_item)
#
# 	return render(request, 'commissioning/punch_item_resolve.html', {
# 			'punch_item': punch_item,
# 			'form': form,
# 			})
#
#
# def punch_item_verify_view(request, pk):
# 	"""Verify a resolved punch item."""
# 	punch_item = get_object_or_404(PunchItem, pk=pk)
#
# 	if request.method == 'POST':
# 		form = PunchItemVerifyForm(request.POST, instance=punch_item)
# 		if form.is_valid():
# 			new_status = form.cleaned_data['status']
# 			form.instance.verified_by = request.user
# 			form.instance.verified_date = timezone.now().date()
# 			form.save()
#
# 			if new_status == 'CLSD':
# 				messages.success(request, f"Punch item {punch_item.punch_number} verified and closed.")
# 			else:
# 				messages.info(request, f"Punch item {punch_item.punch_number} returned to in-progress.")
#
# 			return redirect('commissioning:punch_item_detail', pk=punch_item.pk)
# 	else:
# 		form = PunchItemVerifyForm(instance=punch_item)
#
# 	return render(request, 'commissioning/punch_item_verify.html', {
# 			'punch_item': punch_item,
# 			'form': form,
# 			})
#
#
# class PunchItemPhotoUploadView(BaseCreateView):
# 	"""Upload photo to a punch item."""
# 	model = PunchItemPhoto
# 	form_class = PunchItemPhotoForm
# 	template_name = 'commissioning/punch_item_photo_upload.html'
# 	success_message = "Photo uploaded successfully."
#
# 	def get_success_url(self):
# 		return reverse('commissioning:punch_item_detail', kwargs={'pk': self.kwargs['punch_id']})
#
# 	def form_valid(self, form):
# 		punch = get_object_or_404(PunchItem, pk=self.kwargs['punch_id'])
# 		form.instance.punch_item = punch
# 		return super().form_valid(form)
#