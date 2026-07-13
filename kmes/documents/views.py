from django.db import transaction
from django.http import HttpResponse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from .models import Document, TagDocument, DocumentShare
from .forms import DocumentShareForm, DocumentShareUpdateForm,DocumentForm

class DocumentCreateView(LoginRequiredMixin, generic.CreateView):
	model = Document
	form_class = DocumentForm
	template_name = 'documents/document_form.html'
	success_message = "Document '%(document_number)s' was created successfully."
	
	def get_success_url(self):
		HttpResponse('success')# return reverse('documents:document_detail', kwargs={'pk': self.object.pk})
	
	def get_initial(self):
		initial = super().get_initial()
		project_id = self.kwargs.get('project_id') or self.request.GET.get('project')
		if project_id:
			try:
				from core.models import Project
				initial['project'] = get_object_or_404(Project, pk=project_id)
			except (ImportError, ValueError):
				pass
		
		# Pre-fill some defaults
		initial['revision'] = 'A'
		initial['status'] = 'DRAFT'
		
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = True
		context['page_title'] = 'Upload New Document'
		
		# Get recent documents for reference
		context['recent_documents'] = Document.objects.order_by('-created_at')[:5]
		
		return context
	
	def form_valid(self, form):
		# Set the submitted by user
		form.instance.submitted_by = self.request.user
		
		# Auto-generate document number if not provided
		if not form.instance.document_number:
			form.instance.document_number = self.generate_document_number(form)
		
		# Set issue date if status is approved or IFC
		if form.cleaned_data.get('status') in ['APPR', 'IFC', 'ASBL']:
			form.instance.issue_date = form.instance.issue_date or timezone.now().date()
			if not form.instance.approved_by:
				form.instance.approved_by = self.request.user
		
		messages.success(self.request, self.success_message % {'document_number': form.instance.document_number})
		return super().form_valid(form)
	
	def form_invalid(self, form):
		messages.error(self.request, 'Please correct the errors below.')
		return super().form_invalid(form)
	
	def generate_document_number(self, form):
		"""Generate a document number based on project, type, and discipline."""
		project = form.cleaned_data.get('project')
		doc_type = form.cleaned_data.get('doc_type', 'OTHR')
		discipline = form.cleaned_data.get('discipline', 'GEN')
		
		# Get project code
		project_code = project.code if project else 'GEN'
		
		# Get current year
		year = timezone.now().strftime('%y')
		
		# Count existing documents for this project
		count = Document.objects.filter(
				project=project
				).count() + 1
		
		# Format: PRJ-TYPE-DISC-YY-NNNN
		return f"{project_code}-{doc_type}-{discipline}-{year}-{count:04d}"


class DocumentUpdateView(LoginRequiredMixin, generic.UpdateView):
	model = Document
	form_class = DocumentForm
	template_name = 'documents/document_form.html'
	success_message = "Document '%(document_number)s' was updated successfully."
	
	def get_success_url(self):
		return HttpResponse('success')# return reverse('documents:document_detail', kwargs={'pk': self.object.pk})
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['is_create'] = False
		context['page_title'] = f'Edit Document: {self.object.document_number}'
		return context
	
	def form_valid(self, form):
		# Set approved by if status changed to approved
		old_instance = Document.objects.get(pk=self.object.pk)
		if old_instance.status != form.cleaned_data['status']:
			if form.cleaned_data['status'] in ['APPR', 'IFC']:
				form.instance.approved_by = self.request.user
				form.instance.issue_date = form.instance.issue_date or timezone.now().date()
		
		messages.success(self.request, self.success_message % {'document_number': form.instance.document_number})
		return super().form_valid(form)
	
	def form_invalid(self, form):
		messages.error(self.request, 'Please correct the errors below.')
		return super().form_invalid(form)

class DocumentDetailView(LoginRequiredMixin, generic.DetailView):
	model = Document
	template_name = 'documents/document_detail.html'
	context_object_name = 'document'
	
	def get_queryset(self):
		return Document.objects.select_related(
				'project', 'submitted_by', 'approved_by'
				).prefetch_related(
				'shares__shared_with',
				'shares__shared_by',
				'tag_documents__equipment_tag'
				)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		doc = self.get_object()
		
		# Linked equipment tags
		context['linked_tags'] = doc.tag_documents.select_related(
				'equipment_tag__project', 'equipment_tag__area'
				).all()
		
		# All revisions
		context['revisions'] = Document.objects.filter(
				document_number=doc.document_number
				).order_by('-created_at')
		
		# Check if latest revision
		context['is_latest_revision'] = not Document.objects.filter(
				document_number=doc.document_number,
				created_at__gt=doc.created_at
				).exists()
		
		# Previous and next revisions
		context['previous_revision'] = Document.objects.filter(
				document_number=doc.document_number,
				created_at__lt=doc.created_at
				).order_by('-created_at').first()
		
		context['next_revision'] = Document.objects.filter(
				document_number=doc.document_number,
				created_at__gt=doc.created_at
				).order_by('created_at').first()
		
		# Related documents
		context['related_documents'] = Document.objects.filter(
				project=doc.project
				).exclude(pk=doc.pk).order_by('-created_at')[:10]
		
		# Document shares
		context['shares'] = doc.shares.select_related(
				'shared_with', 'shared_by'
				).order_by('-shared_date')
		
		context['total_shares'] = doc.shares.count()
		context['viewed_shares'] = doc.shares.filter(is_accessed=True).count()
		context['unviewed_shares'] = doc.shares.filter(is_accessed=False).count()
		
		# Check if current user can share
		context['can_share'] = (
				self.request.user.is_staff or
				doc.submitted_by == self.request.user
		)
		
		# Check if this document was shared with current user
		context['is_shared_with_me'] = doc.shares.filter(
				shared_with=self.request.user
				).exists()
		
		if context['is_shared_with_me']:
			# Mark as accessed
			doc.shares.filter(
					shared_with=self.request.user,
					is_accessed=False
					).update(
					is_accessed=True,
					accessed_date=timezone.now()
					)
			
			# Get my share permissions
			context['my_share'] = doc.shares.filter(
					shared_with=self.request.user
					).first()
		
		# File information
		if doc.file_upload:
			import os
			context['file_extension'] = os.path.splitext(doc.file_upload.name)[1].lower()
			try:
				context['file_size'] = doc.file_upload.size
			except:
				context['file_size'] = None
		
		# Activities
		context['activities'] = self.get_document_activities(doc)
		
		return context
	
	def get_document_activities(self, doc):
		"""Get activity history for the document including shares."""
		activities = []
		
		# Revision activities
		revisions = Document.objects.filter(
				document_number=doc.document_number
				).order_by('-created_at')
		
		for revision in revisions:
			activities.append({
					'icon': 'file-earmark-text',
					'description': f'Revision {revision.revision} created',
					'status': revision.get_status_display(),
					'date': revision.created_at,
					'user': revision.submitted_by.get_full_name() if revision.submitted_by else 'System',
					'type': 'revision'
					})
		
		# Share activities
		shares = doc.shares.all().order_by('-shared_date')
		for share in shares:
			activities.append({
					'icon': 'share',
					'description': f'Shared with {share.shared_with.get_full_name() or share.shared_with.username}',
					'status': 'Can Edit' if share.can_edit else 'View Only',
					'date': share.shared_date,
					'user': share.shared_by.get_full_name() if share.shared_by else 'System',
					'type': 'share',
					'accessed': share.is_accessed
					})
		
		# Tag linking activities
		tag_links = doc.tag_documents.all().order_by('-added_date')
		for link in tag_links:
			activities.append({
					'icon': 'link-45deg',
					'description': f'Linked to tag {link.equipment_tag.tag_number}',
					'status': link.relation_type,
					'date': link.added_date,
					'user': 'System',
					'type': 'link'
					})
		
		# Sort by date
		activities.sort(key=lambda x: x['date'], reverse=True)
		return activities[:20]
	def document_share_view(request, pk):
		"""Share a document with other users."""
		document = get_object_or_404(Document, pk=pk)
		
		# Check if user can share (is admin or document owner)
		if not request.user.is_staff and document.submitted_by != request.user:
			messages.error(request, "You don't have permission to share this document.")
			return redirect('documents:document_detail', pk=document.pk)
		
		if request.method == 'POST':
			form = DocumentShareForm(request.POST, document=document, user=request.user)
			if form.is_valid():
				users = form.cleaned_data['users']
				can_edit = form.cleaned_data['can_edit']
				message = form.cleaned_data['message']
				
				shared_count = 0
				with transaction.atomic():
					for user in users:
						DocumentShare.objects.create(
								document=document,
								shared_by=request.user,
								shared_with=user,
								can_edit=can_edit,
								message=message
								)
						shared_count += 1
				
				if shared_count > 0:
					messages.success(
							request,
							f"Document shared successfully with {shared_count} user(s)."
							)
				return redirect('documents:document_detail', pk=document.pk)
		else:
			form = DocumentShareForm(document=document, user=request.user)
		
		# Get existing shares
		existing_shares = DocumentShare.objects.filter(
				document=document
				).select_related('shared_with', 'shared_by')
		
		return render(request, 'documents/document_share.html', {
				'document': document,
				'form': form,
				'existing_shares': existing_shares
				})


	
	def document_share_update_view(request, pk):
		"""Update share permissions."""
		share = get_object_or_404(DocumentShare, pk=pk)
		
		# Check permissions
		if request.user != share.shared_by and not request.user.is_staff:
			messages.error(request, "You don't have permission to update this share.")
			return redirect('documents:document_detail', pk=share.document.pk)
		
		if request.method == 'POST':
			form = DocumentShareUpdateForm(request.POST, instance=share)
			if form.is_valid():
				form.save()
				messages.success(request, "Share permissions updated successfully.")
				return redirect('documents:document_share', pk=share.document.pk)
		else:
			form = DocumentShareUpdateForm(instance=share)
		
		return render(request, 'documents/document_share_update.html', {
				'share': share,
				'form': form,
				'document': share.document
				})


	
	def document_share_delete_view(request, pk):
		"""Remove document sharing."""
		share = get_object_or_404(DocumentShare, pk=pk)
		
		# Check permissions
		if request.user != share.shared_by and not request.user.is_staff:
			messages.error(request, "You don't have permission to remove this share.")
			return redirect('documents:document_detail', pk=share.document.pk)
		
		document_pk = share.document.pk
		
		if request.method == 'POST':
			share.delete()
			messages.success(request, "Document share removed successfully.")
			return redirect('documents:document_share', pk=document_pk)
		
		return render(request, 'documents/document_share_delete.html', {
				'share': share,
				'document': share.document
				})

	
	
	def shared_with_me_view(request):
		"""View documents shared with the current user."""
		shares = DocumentShare.objects.filter(
				shared_with=request.user
				).select_related(
				'document__project', 'shared_by'
				).order_by('-shared_date')
		
		return render(request, 'documents/shared_with_me.html', {
				'shares': shares,
				'unread_count': shares.filter(is_accessed=False).count()
				})