from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db import models as db_models

from documents.models import Document, TagDocument
from core.models import Project, EquipmentTag
from documents.forms import (
	DocumentForm, DocumentRevisionForm, TagDocumentForm,
	DocumentSearchForm, DocumentBulkUploadForm
	)
from ..base_views import BaseCreateView, BaseUpdateView, BaseDeleteView


# ============================================
# DOCUMENT VIEWS
# ============================================

class DocumentListView(LoginRequiredMixin, generic.ListView):
	model = Document
	template_name = 'documents/document_list.html'
	context_object_name = 'documents'
	paginate_by = 25
	
	def get_queryset(self):
		queryset = Document.objects.select_related('project', 'submitted_by')
		form = DocumentSearchForm(self.request.GET)
		
		if form.is_valid():
			data = form.cleaned_data
			if data.get('project'):
				queryset = queryset.filter(project=data['project'])
			if data.get('doc_type'):
				queryset = queryset.filter(doc_type=data['doc_type'])
			if data.get('discipline'):
				queryset = queryset.filter(discipline=data['discipline'])
			if data.get('status'):
				queryset = queryset.filter(status=data['status'])
			if data.get('search'):
				search = data['search']
				queryset = queryset.filter(
						db_models.Q(document_number__icontains=search) |
						db_models.Q(title__icontains=search)
						)
		
		return queryset.order_by('-created_at')
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['search_form'] = DocumentSearchForm(self.request.GET)
		return context


class DocumentDetailView(LoginRequiredMixin, generic.DetailView):
	model = Document
	template_name = 'documents/document_detail.html'
	context_object_name = 'document'
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		doc = self.get_object()
		context['linked_tags'] = doc.tag_documents.select_related('equipment_tag').all()
		context['is_latest_revision'] = not Document.objects.filter(
				document_number=doc.document_number,
				created_at__gt=doc.created_at
				).exists()
		return context


class DocumentCreateView(BaseCreateView):
	model = Document
	form_class = DocumentForm
	template_name = 'documents/document_form.html'
	success_message = "Document '%(document_number)s' was created successfully."
	
	def get_success_url(self):
		return reverse('documents:document_detail', kwargs={'pk': self.object.pk})
	
	def get_initial(self):
		initial = super().get_initial()
		project_id = self.kwargs.get('project_id')
		if project_id:
			initial['project'] = get_object_or_404(Project, pk=project_id)
		return initial
	
	def form_valid(self, form):
		form.instance.submitted_by = self.request.user
		return super().form_valid(form)


class DocumentUpdateView(BaseUpdateView):
	model = Document
	form_class = DocumentForm
	template_name = 'documents/document_form.html'
	success_message = "Document '%(document_number)s' was updated successfully."
	
	def get_success_url(self):
		return reverse('documents:document_detail', kwargs={'pk': self.object.pk})


class DocumentDeleteView(BaseDeleteView):
	model = Document
	template_name = 'documents/document_confirm_delete.html'
	success_url = reverse_lazy('documents:document_list')
	success_message = "Document was deleted successfully."


class DocumentRevisionCreateView(BaseCreateView):
	"""Create a new revision of an existing document."""
	model = Document
	form_class = DocumentRevisionForm
	template_name = 'documents/document_revision_form.html'
	success_message = "New revision of '%(document_number)s' was created successfully."
	
	def get_initial(self):
		initial = super().get_initial()
		original_doc = get_object_or_404(Document, pk=self.kwargs['pk'])
		# Copy fields from original document
		for field in ['project', 'document_number', 'title', 'doc_type', 'discipline', 'file_path']:
			initial[field] = getattr(original_doc, field)
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['original_document'] = get_object_or_404(Document, pk=self.kwargs['pk'])
		return context
	
	def get_success_url(self):
		return reverse('documents:document_detail', kwargs={'pk': self.object.pk})
	
	def form_valid(self, form):
		# Mark the old revision as superseded if the new one is approved
		if form.cleaned_data.get('status') in ['APPR', 'IFC']:
			original = get_object_or_404(Document, pk=self.kwargs['pk'])
			if original.status in ['APPR', 'IFC', 'ASBL']:
				original.status = 'SUPD'
				original.save()
		
		form.instance.submitted_by = self.request.user
		return super().form_valid(form)


# ============================================
# TAG-DOCUMENT RELATIONSHIP VIEWS
# ============================================

class TagDocumentCreateView(BaseCreateView):
	model = TagDocument
	form_class = TagDocumentForm
	template_name = 'documents/tag_document_form.html'
	success_message = "Document linked to tag successfully."
	
	def get_success_url(self):
		if self.object.equipment_tag:
			return reverse('core:equipment_tag_detail', kwargs={'pk': self.object.equipment_tag.pk})
		return reverse('documents:document_detail', kwargs={'pk': self.object.document.pk})


class TagDocumentDeleteView(BaseDeleteView):
	model = TagDocument
	template_name = 'documents/tag_document_confirm_delete.html'
	success_message = "Document link removed successfully."
	
	def get_success_url(self):
		obj = self.get_object()
		return reverse('core:equipment_tag_detail', kwargs={'pk': obj.equipment_tag.pk})


# ============================================
# BULK UPLOAD VIEW
# ============================================
#
# def document_bulk_upload_view(request):
# 	"""Handle bulk upload of multiple documents."""
# 	if request.method == 'POST':
# 		form = DocumentBulkUploadForm(request.POST, request.FILES)
# 		if form.is_valid():
# 			project = form.cleaned_data['project']
# 			files = request.FILES.getlist('files')
#
# 			created_count = 0
# 			for file in files:
# 				Document.objects.create(
# 						project=project,
# 						document_number=file.name.rsplit('.', 1)[0],
# 						title=file.name,
# 						doc_type='OTHR',
# 						discipline='GEN',
# 						revision='A',
# 						file_upload=file,
# 						submitted_by=request.user
# 						)
# 				created_count += 1
#
# 			messages.success(request, f"Successfully uploaded {created_count} documents.")
# 			return redirect('documents:document_list')
# 	else:
# 		form = DocumentBulkUploadForm()
#
# 	return render(request, 'documents/document_bulk_upload.html', {'form': form})
def document_bulk_upload_view(request):
	"""Handle bulk upload of multiple documents."""
	if request.method == 'POST':
		form = DocumentBulkUploadForm(request.POST, request.FILES)
		if form.is_valid():
			project = form.cleaned_data['project']
			files = form.cleaned_data['files']
			
			# files will be a list if multiple files were selected
			if not isinstance(files, (list, tuple)):
				files = [files]
			
			created_count = 0
			for file in files:
				# Generate document number from filename (without extension)
				doc_number = file.name.rsplit('.', 1)[0] if '.' in file.name else file.name
				
				Document.objects.create(
						project=project,
						document_number=doc_number,
						title=file.name,
						doc_type='OTHR',
						discipline='GEN',
						revision='A',
						file_upload=file,
						submitted_by=request.user
						)
				created_count += 1
			
			messages.success(request, f"Successfully uploaded {created_count} documents.")
			return redirect('document_list')
	else:
		form = DocumentBulkUploadForm()
	
	return render(request, 'documents/document_bulk_upload.html', {'form': form})