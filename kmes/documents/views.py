from datetime import timezone, time, datetime
from time import timezone as ttimezone
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from .models import Document, TagDocument, DocumentShare, DocumentDownload
from .forms import DocumentShareForm, DocumentShareUpdateForm, DocumentForm, TagDocumentForm, TagDocumentBulkForm, DocumentSearchForm
from django.http import JsonResponse
import os
import mimetypes
from django.http import FileResponse, Http404, StreamingHttpResponse
from wsgiref.util import FileWrapper
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Case, When, Value, CharField


User = get_user_model()

class DocumentCreateView(LoginRequiredMixin, generic.CreateView):
	model = Document
	form_class = DocumentForm
	template_name = 'documents/document_form.html'
	success_message = "Document '%(document_number)s' was created successfully."
	
	def get_success_url(self):
		HttpResponse('success')  # return reverse('documents:document_detail', kwargs={'pk': self.object.pk})
	
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
	

class DocumentListView(LoginRequiredMixin, generic.ListView):
	model = Document
	template_name = 'documents/document_list.html'
	context_object_name = 'documents'
	paginate_by = 20
	
	def get_queryset(self):
		queryset = Document.objects.select_related(
				'project', 'submitted_by', 'approved_by'
				).prefetch_related(
				'tag_documents__equipment_tag',
				'shares'
				).annotate(
				linked_tags_count=Count('tag_documents', distinct=True),
				shares_count=Count('shares', distinct=True),
				unviewed_shares_count=Count(
						Case(
								When(shares__is_accessed=False, then=1),
								output_field=CharField(),
								),
						distinct=True
						)
				)
		
		# Apply filters from search form
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
						Q(document_number__icontains=search) |
						Q(title__icontains=search) |
						Q(notes__icontains=search) |
						Q(tag_documents__equipment_tag__tag_number__icontains=search)
						).distinct()
			
			if data.get('date_from'):
				queryset = queryset.filter(created_at__date__gte=data['date_from'])
			
			if data.get('date_to'):
				queryset = queryset.filter(created_at__date__lte=data['date_to'])
			
			if data.get('has_file'):
				queryset = queryset.filter(file_upload__isnull=False)
		
		# Apply sorting
		sort = self.request.GET.get('sort', '-created_at')
		allowed_sorts = [
				'document_number', '-document_number',
				'title', '-title',
				'doc_type', '-doc_type',
				'status', '-status',
				'revision', '-revision',
				'created_at', '-created_at',
				'updated_at', '-updated_at',
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
		
		# Search/filter form
		context['search_form'] = DocumentSearchForm(self.request.GET)
		
		# View mode (table or card)
		context['view_mode'] = self.request.GET.get('view', 'table')
		
		# Statistics
		base_queryset = Document.objects.all()
		project_id = self.request.GET.get('project')
		if project_id:
			base_queryset = base_queryset.filter(project_id=project_id)
		
		context['total_documents'] = base_queryset.count()
		context['approved_documents'] = base_queryset.filter(status='APPR').count()
		context['ifc_documents'] = base_queryset.filter(status='IFC').count()
		context['draft_documents'] = base_queryset.filter(status='DRAFT').count()
		context['superseded_documents'] = base_queryset.filter(status='SUPD').count()
		context['review_documents'] = base_queryset.filter(status='REVW').count()
		
		# Documents with files vs without
		context['documents_with_files'] = base_queryset.filter(file_upload__isnull=False).count()
		context['documents_without_files'] = base_queryset.filter(file_upload__isnull=True, file_path='').count()
		
		# Document type distribution
		context['doc_type_distribution'] = base_queryset.values(
				'doc_type'
				).annotate(count=Count('id')).order_by('-count')
		
		# Recent uploads
		context['recent_uploads'] = base_queryset.order_by('-created_at')[:5]
		
		# Most linked documents
		context['most_linked_documents'] = base_queryset.annotate(
				link_count=Count('tag_documents')
				).filter(link_count__gt=0).order_by('-link_count')[:10]
		
		# Projects for filter dropdown
		try:
			from core.models import Project
			context['projects'] = Project.objects.all()
		except ImportError:
			context['projects'] = []
		
		# Current time for relative date display
		context['now'] = datetime.now()
		
		return context


class DocumentUpdateView(LoginRequiredMixin, generic.UpdateView):
	model = Document
	form_class = DocumentForm
	template_name = 'documents/document_form.html'
	success_message = "Document '%(document_number)s' was updated successfully."
	
	def get_success_url(self):
		return HttpResponse('success')  # return reverse('documents:document_detail', kwargs={'pk': self.object.pk})
	
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
			activities.append(
					{
							'icon':        'file-earmark-text',
							'description': f'Revision {revision.revision} created',
							'status':      revision.get_status_display(),
							'date':        revision.created_at,
							'user':        revision.submitted_by.get_full_name() if revision.submitted_by else 'System',
							'type':        'revision'
							}
					)
		
		# Share activities
		shares = doc.shares.all().order_by('-shared_date')
		for share in shares:
			activities.append(
					{
							'icon':        'share',
							'description': f'Shared with {share.shared_with.get_full_name() or share.shared_with.username}',
							'status':      'Can Edit' if share.can_edit else 'View Only',
							'date':        share.shared_date,
							'user':        share.shared_by.get_full_name() if share.shared_by else 'System',
							'type':        'share',
							'accessed':    share.is_accessed
							}
					)
		
		# Tag linking activities
		tag_links = doc.tag_documents.all().order_by('-added_date')
		for link in tag_links:
			
			activities.append(
					{
							'icon':        'link-45deg',
							'description': f'Linked to tag {link.equipment_tag.tag_number}',
							'status':      link.relation_type,
							'date':        link.added_date,
							'user':        'System',
							'type':        'link'
							}
					)
		
		# Sort by date
		# activities.sort(key=lambda x: x['date'], reverse=True)
		return activities[:20]


def document_share_view(request, pk):
	"""Share a document with other users."""
	document = get_object_or_404(Document, pk=pk)
	
	# # Check if user can share (is admin or document owner)
	# if not request.user.is_staff and document.submitted_by != request.user:
	# 	messages.error(request, "You don't have permission to share this document.")
	# 	return redirect('documents:document_detail', pk=document.pk)
	
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
	
	return render(
		request, 'documents/document_share.html', {
					'document':        document,
					'form':            form,
					'existing_shares': existing_shares
					}
		)


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
	
	return render(
		request, 'documents/document_share_update.html', {
					'share':    share,
					'form':     form,
					'document': share.document
					}
		)


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
	
	return render(
		request, 'documents/document_share_delete.html', {
					'share':    share,
					'document': share.document
					}
		)


def shared_with_me_view(request):
	"""
	View documents shared with the current user.
	Includes options to mark documents as seen/read.
	"""
	shares = DocumentShare.objects.filter(
			shared_with=request.user
			).select_related(
			'document__project',
			'document__submitted_by',
			'shared_by'
			).prefetch_related(
			'document__tag_documents__equipment_tag'
			).order_by('-shared_date')
	
	# Statistics
	total_shared = shares.count()
	unread_count = shares.filter(is_accessed=False).count()
	read_count = shares.filter(is_accessed=True).count()
	
	# Get filter from query params
	filter_type = request.GET.get('filter', 'all')
	
	if filter_type == 'unread':
		shares = shares.filter(is_accessed=False)
	elif filter_type == 'read':
		shares = shares.filter(is_accessed=True)
	
	# Search
	search = request.GET.get('search', '')
	if search:
		shares = shares.filter(
				Q(document__document_number__icontains=search) |
				Q(document__title__icontains=search) |
				Q(shared_by__first_name__icontains=search) |
				Q(shared_by__last_name__icontains=search) |
				Q(message__icontains=search)
				)
	
	# Sort
	sort = request.GET.get('sort', '-shared_date')
	allowed_sorts = [
			'shared_date', '-shared_date',
			'document__document_number', '-document__document_number',
			'document__title', '-document__title',
			'is_accessed', '-is_accessed',
			]
	if sort in allowed_sorts:
		shares = shares.order_by(sort)
	
	context = {
			'shares': shares,
			'total_shared': total_shared,
			'unread_count': unread_count,
			'read_count': read_count,
			'filter_type': filter_type,
			'search': search,
			'page_title': 'Documents Shared With Me',
			}
	
	return render(request, 'documents/shared_with_me.html', context)


def mark_document_as_seen(request, pk):
	"""Mark a shared document as seen/read."""
	share = get_object_or_404(
			DocumentShare,
			pk=pk,
			shared_with=request.user
			)
	
	if not share.is_accessed:
		share.is_accessed = True
		share.accessed_date = timezone.now()
		share.save()
		
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
					'success': True,
					'message': 'Document marked as seen.',
					'accessed_date': share.accessed_date.strftime('%b %d, %Y %H:%M')
					})
		
		messages.success(request, 'Document marked as seen.')
	else:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
					'success': False,
					'message': 'Document was already marked as seen.'
					})
	
	# Redirect back to the referring page
	referer = request.META.get('HTTP_REFERER')
	if referer:
		return redirect(referer)
	return redirect('documents:shared_with_me')


def mark_all_as_seen(request):
	"""Mark all shared documents as seen."""
	if request.method == 'POST':
		updated_count = DocumentShare.objects.filter(
				shared_with=request.user,
				is_accessed=False
				).update(
				is_accessed=True,
				accessed_date=timezone.now()
				)
		
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
					'success': True,
					'message': f'{updated_count} document(s) marked as seen.',
					'count': updated_count
					})
		
		messages.success(
				request,
				f'{updated_count} document(s) marked as seen.'
				)
	
	return redirect('documents:shared_with_me')


def mark_document_as_unread(request, pk):
	"""Mark a shared document as unread."""
	share = get_object_or_404(
			DocumentShare,
			pk=pk,
			shared_with=request.user
			)
	
	if share.is_accessed:
		share.is_accessed = False
		share.accessed_date = None
		share.save()
		
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
					'success': True,
					'message': 'Document marked as unread.'
					})
		
		messages.success(request, 'Document marked as unread.')
	
	return redirect('documents:shared_with_me')


def document_share_resend_view(request, pk):
	"""Resend share notification to a user."""
	share = get_object_or_404(DocumentShare, pk=pk)
	
	# Check permissions
	if request.user != share.shared_by and not request.user.is_staff:
		messages.error(request, "You don't have permission to resend this share.")
		return redirect('documents:document_detail', pk=share.document.pk)
	
	# Reset the shared date to trigger a new notification
	share.shared_date = timezone.now()
	share.is_accessed = False
	share.accessed_date = None
	share.save()
	
	# Here you could add email notification logic
	# send_share_notification(share)
	
	messages.success(
			request,
			f"Share notification resent to {share.shared_with.get_full_name() or share.shared_with.username}."
			)
	return redirect('documents:document_share', pk=share.document.pk)



def shared_by_me_view(request):
	"""View documents shared by the current user."""
	shares = DocumentShare.objects.filter(
			shared_by=request.user
			).select_related(
			'document__project', 'shared_with'
			).order_by('-shared_date')
	
	# Statistics
	total_shared = shares.count()
	viewed_count = shares.filter(is_accessed=True).count()
	pending_count = shares.filter(is_accessed=False).count()
	
	return render(
		request, 'documents/shared_by_me.html', {
					'shares':        shares,
					'total_shared':  total_shared,
					'viewed_count':  viewed_count,
					'pending_count': pending_count,
					}
		)



def document_bulk_share_view(request):
	"""Bulk share multiple documents with users."""
	if request.method == 'POST':
		document_ids = request.POST.getlist('documents')
		user_ids = request.POST.getlist('users')
		can_edit = request.POST.get('can_edit') == 'on'
		message_text = request.POST.get('message', '')
		
		if not document_ids:
			messages.error(request, "Please select at least one document.")
			return redirect('documents:document_list')
		
		if not user_ids:
			messages.error(request, "Please select at least one user.")
			return redirect('documents:document_list')
		
		documents = Document.objects.filter(pk__in=document_ids)
		users = User.objects.filter(pk__in=user_ids, is_active=True)
		
		shared_count = 0
		with transaction.atomic():
			for document in documents:
				for user in users:
					# Check if user can share this document
					if request.user.is_staff or document.submitted_by == request.user:
						_, created = DocumentShare.objects.get_or_create(
								document=document,
								shared_with=user,
								defaults={
										'shared_by': request.user,
										'can_edit':  can_edit,
										'message':   message_text
										}
								)
						if created:
							shared_count += 1
		
		messages.success(
				request,
				f"Successfully shared {shared_count} document(s) with {len(users)} user(s)."
				)
		return redirect('documents:document_list')
	
	# GET request - show form
	documents = Document.objects.all()
	users = User.objects.filter(is_active=True)
	
	return render(
		request, 'documents/document_bulk_share.html', {
					'documents': documents,
					'users':     users,
					}
		)



def ajax_search_users(request):
	"""AJAX endpoint to search users for sharing."""
	search = request.GET.get('q', '')
	
	queryset = User.objects.filter(is_active=True)
	
	if search:
		from django.db.models import Q
		queryset = queryset.filter(
				Q(username__icontains=search) |
				Q(first_name__icontains=search) |
				Q(last_name__icontains=search) |
				Q(email__icontains=search)
				)
	
	# Exclude current user
	queryset = queryset.exclude(pk=request.user.pk)
	
	results = []
	for user in queryset[:20]:
		results.append(
				{
						'id':        user.pk,
						'text':      f"{user.get_full_name() or user.username} ({user.email})",
						'username':  user.username,
						'full_name': user.get_full_name(),
						'email':     user.email,
						}
				)
	
	return JsonResponse({'results': results})


class TagDocumentCreateView(LoginRequiredMixin, generic.CreateView):
	"""
	Link an existing document to an equipment tag.
	Can be accessed from either the tag detail page or document detail page.
	"""
	model = TagDocument
	form_class = TagDocumentForm
	template_name = 'documents/tag_document_form.html'
	success_message = "Document linked to equipment tag successfully."
	
	def get_success_url(self):
		# Redirect based on where the user came from
		if self.object.equipment_tag and self.request.GET.get('from') != 'document':
			return reverse('core:equipment_tag_detail', kwargs={'pk': self.object.equipment_tag.pk})
		elif self.object.document:
			return reverse('documents:document_detail', kwargs={'pk': self.object.document.pk})
		return reverse('core:dashboard')
	
	def get_initial(self):
		initial = super().get_initial()
		
		# Pre-select tag if coming from tag detail
		tag_id = self.request.GET.get('tag')
		if tag_id:
			try:
				from core.models import EquipmentTag
				tag = get_object_or_404(EquipmentTag, pk=tag_id)
				initial['equipment_tag'] = tag
			except (ImportError, ValueError):
				pass
		
		# Pre-select document if coming from document detail
		doc_id = self.request.GET.get('document')
		if doc_id:
			try:
				doc = get_object_or_404(Document, pk=doc_id)
				initial['document'] = doc
			except ValueError:
				pass
		
		# Set default relation type
		initial['relation_type'] = 'references'
		
		return initial
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['page_title'] = 'Link Document to Equipment Tag'
		
		# Get tag or document info for context
		tag_id = self.request.GET.get('tag')
		doc_id = self.request.GET.get('document')
		
		if tag_id:
			try:
				from core.models import EquipmentTag
				context['equipment_tag'] = get_object_or_404(EquipmentTag, pk=tag_id)
				# Get already linked documents
				context['linked_documents'] = TagDocument.objects.filter(
						equipment_tag_id=tag_id
						).select_related('document')
			except (ImportError, ValueError):
				pass
		
		if doc_id:
			context['document'] = get_object_or_404(Document, pk=doc_id)
			# Get tags already linked to this document
			context['linked_tags'] = TagDocument.objects.filter(
					document_id=doc_id
					).select_related('equipment_tag')
		
		return context
	
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		
		# Pass project_id for filtering
		tag_id = self.request.GET.get('tag')
		if tag_id:
			try:
				from core.models import EquipmentTag
				tag = get_object_or_404(EquipmentTag, pk=tag_id)
				kwargs['project_id'] = tag.project_id
			except (ImportError, ValueError):
				pass
		
		doc_id = self.request.GET.get('document')
		if doc_id:
			doc = get_object_or_404(Document, pk=doc_id)
			kwargs['project_id'] = doc.project_id
		
		return kwargs
	
	def form_valid(self, form):
		# Check if link already exists
		equipment_tag = form.cleaned_data['equipment_tag']
		document = form.cleaned_data['document']
		
		existing_link = TagDocument.objects.filter(
				equipment_tag=equipment_tag,
				document=document
				).first()
		
		if existing_link:
			messages.warning(
					self.request,
					f'Document "{document.document_number}" is already linked to tag "{equipment_tag.tag_number}".'
					)
			# Update the relation type if different
			if existing_link.relation_type != form.cleaned_data['relation_type']:
				existing_link.relation_type = form.cleaned_data['relation_type']
				existing_link.save()
				messages.info(self.request, 'Relation type updated.')
			return redirect(self.get_success_url())
		
		messages.success(self.request, self.success_message)
		return super().form_valid(form)


class TagDocumentDeleteView(LoginRequiredMixin, generic.DeleteView):
	"""Remove the link between a document and an equipment tag."""
	model = TagDocument
	template_name = 'documents/tag_document_confirm_delete.html'
	success_message = "Document link removed successfully."
	
	def get_success_url(self):
		obj = self.get_object()
		if self.request.GET.get('redirect') == 'document':
			return reverse('documents:document_detail', kwargs={'pk': obj.document.pk})
		return reverse('core:equipment_tag_detail', kwargs={'pk': obj.equipment_tag.pk})
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['tag_document'] = self.get_object()
		return context
	
	def delete(self, request, *args, **kwargs):
		obj = self.get_object()
		messages.success(request, f'Document "{obj.document.document_number}" unlinked from tag "{obj.equipment_tag.tag_number}".')
		return super().delete(request, *args, **kwargs)


def tag_document_bulk_link_view(request):
	"""
	Bulk link multiple documents to an equipment tag,
	or link a document to multiple equipment tags.
	"""
	if request.method == 'POST':
		form = TagDocumentBulkForm(request.POST)
		if form.is_valid():
			mode = form.cleaned_data['mode']
			relation_type = form.cleaned_data['relation_type']
			
			linked_count = 0
			skipped_count = 0
			
			with transaction.atomic():
				if mode == 'tags_to_document':
					# Link one document to multiple tags
					document = form.cleaned_data['document']
					tags = form.cleaned_data['equipment_tags']
					
					for tag in tags:
						_, created = TagDocument.objects.get_or_create(
								equipment_tag=tag,
								document=document,
								defaults={'relation_type': relation_type}
								)
						if created:
							linked_count += 1
						else:
							skipped_count += 1
					
					messages.success(
							request,
							f'Document linked to {linked_count} tag(s). {skipped_count} already linked.'
							)
					return redirect('documents:document_detail', pk=document.pk)
				
				elif mode == 'documents_to_tag':
					# Link multiple documents to one tag
					tag = form.cleaned_data['equipment_tag']
					documents = form.cleaned_data['documents']
					
					for doc in documents:
						_, created = TagDocument.objects.get_or_create(
								equipment_tag=tag,
								document=doc,
								defaults={'relation_type': relation_type}
								)
						if created:
							linked_count += 1
						else:
							skipped_count += 1
					
					messages.success(
							request,
							f'{linked_count} document(s) linked to tag. {skipped_count} already linked.'
							)
					return redirect('core:equipment_tag_detail', pk=tag.pk)
	else:
		form = TagDocumentBulkForm()
	
	return render(
		request, 'documents/tag_document_bulk_form.html', {
					'form':       form,
					'page_title': 'Bulk Link Documents & Tags'
					}
		)


def ajax_search_tags(request):
	"""AJAX endpoint to search equipment tags."""
	search = request.GET.get('q', '')
	project_id = request.GET.get('project')
	
	try:
		from core.models import EquipmentTag
		queryset = EquipmentTag.objects.all()
		
		if project_id:
			queryset = queryset.filter(project_id=project_id)
		
		if search:
			queryset = queryset.filter(
					Q(tag_number__icontains=search) |
					Q(description__icontains=search)
					)
		
		results = []
		for tag in queryset[:20]:
			results.append(
					{
							'id':             tag.pk,
							'text':           f'{tag.tag_number} - {tag.description[:60]}',
							'tag_number':     tag.tag_number,
							'description':    tag.description[:100],
							'equipment_type': tag.get_equipment_type_display(),
							'status':         tag.get_status_display(),
							}
					)
		
		return JsonResponse({'results': results})
	except ImportError:
		return JsonResponse({'results': [], 'error': 'Core app not available'}, status=500)


def ajax_search_documents(request):
	"""AJAX endpoint to search documents."""
	search = request.GET.get('q', '')
	project_id = request.GET.get('project')
	
	queryset = Document.objects.all()
	
	if project_id:
		queryset = queryset.filter(project_id=project_id)
	
	if search:
		queryset = queryset.filter(
				Q(document_number__icontains=search) |
				Q(title__icontains=search)
				)
	
	results = []
	for doc in queryset[:20]:
		results.append(
				{
						'id':              doc.pk,
						'text':            f'{doc.document_number} - {doc.title[:60]}',
						'document_number': doc.document_number,
						'title':           doc.title[:100],
						'doc_type':        doc.get_doc_type_display(),
						'status':          doc.get_status_display(),
						'revision':        doc.revision,
						}
				)
	
	return JsonResponse({'results': results})


def tag_document_list_view(request):
	"""View all document-tag relationships."""
	links = TagDocument.objects.select_related(
			'equipment_tag__project',
			'equipment_tag__area',
			'document__project'
			).order_by('-added_date')
	
	# Filters
	project_id = request.GET.get('project')
	if project_id:
		links = links.filter(
				Q(equipment_tag__project_id=project_id) |
				Q(document__project_id=project_id)
				)
	
	relation_type = request.GET.get('relation_type')
	if relation_type:
		links = links.filter(relation_type=relation_type)
	
	search = request.GET.get('search')
	if search:
		links = links.filter(
				Q(equipment_tag__tag_number__icontains=search) |
				Q(equipment_tag__description__icontains=search) |
				Q(document__document_number__icontains=search) |
				Q(document__title__icontains=search)
				)
	
	return render(
		request, 'documents/tag_document_list.html', {
					'links':      links,
					'page_title': 'Document-Tag Relationships',
					}
		)


def document_download_view(request, pk):
	"""
	Download a document file.
	Handles both uploaded files and file paths.
	Tracks download activity.
	"""
	document = get_object_or_404(Document, pk=pk)
	
	# Check if user has permission to download
	if not can_user_download_document(request.user, document):
		messages.error(request, "You don't have permission to download this document.")
		return redirect('documents:document_detail', pk=document.pk)
	
	# Handle uploaded file
	if document.file_upload:
		return download_uploaded_file(request, document)
	
	# Handle external file path
	elif document.file_path:
		return download_external_file(request, document)
	
	else:
		messages.error(request, "No file is attached to this document.")
		return redirect('documents:document_detail', pk=document.pk)


def can_user_download_document(user, document):
	"""
	Check if a user has permission to download a document.
	Users can download if:
	- They are staff/admin
	- They are the document submitter
	- The document has been shared with them
	- The document is approved/IFC (public)
	"""
	if user.is_staff or user.is_superuser:
		return True
	
	if document.submitted_by == user:
		return True
	
	if document.approved_by == user:
		return True
	
	# Check if shared with user
	if DocumentShare.objects.filter(
			document=document,
			shared_with=user
			).exists():
		return True
	
	# Public documents (approved or IFC)
	if document.status in ['APPR', 'IFC', 'ASBL']:
		return True
	
	return False


def download_uploaded_file(request, document):
	"""
	Download a file that was uploaded to the server.
	Supports streaming for large files.
	"""
	file_path = document.file_upload.path
	
	# Check if file exists
	if not os.path.exists(file_path):
		messages.error(request, "File not found on the server. It may have been moved or deleted.")
		return redirect('documents:document_detail', pk=document.pk)
	
	# Get file information
	file_size = os.path.getsize(file_path)
	file_name = os.path.basename(file_path)
	
	# Determine content type
	content_type = get_content_type(file_path)
	
	# For large files (>50MB), use streaming
	if file_size > 50 * 1024 * 1024:  # 50MB
		return stream_large_file(request, document, file_path, file_name, content_type, file_size)
	
	# For smaller files, use FileResponse
	try:
		response = FileResponse(
				open(file_path, 'rb'),
				content_type=content_type,
				as_attachment=True,
				filename=file_name
				)
		
		# Set additional headers
		response['Content-Length'] = file_size
		response['Content-Disposition'] = f'attachment; filename="{file_name}"'
		
		# Prevent caching for sensitive documents
		if document.status not in ['APPR', 'IFC', 'ASBL']:
			response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
			response['Pragma'] = 'no-cache'
			response['Expires'] = '0'
		
		# Track download
		track_document_download(request, document)
		
		return response
	
	except Exception as e:
		messages.error(request, f"Error downloading file: {str(e)}")
		return redirect('documents:document_detail', pk=document.pk)


def stream_large_file(request, document, file_path, file_name, content_type, file_size):
	"""
	Stream large files to avoid loading them entirely into memory.
	"""
	try:
		# Open file in binary mode
		file_handle = open(file_path, 'rb')
		
		# Create streaming response
		response = StreamingHttpResponse(
				FileWrapper(file_handle),
				content_type=content_type
				)
		
		# Set headers
		response['Content-Disposition'] = f'attachment; filename="{file_name}"'
		response['Content-Length'] = file_size
		
		# Track download
		track_document_download(request, document)
		
		return response
	
	except Exception as e:
		messages.error(request, f"Error streaming file: {str(e)}")
		return redirect('documents:document_detail', pk=document.pk)


def download_external_file(request, document):
	"""
	Handle download for documents with external file paths.
	"""
	file_path = document.file_path
	
	# Check if it's a network path
	if file_path.startswith('\\\\') or file_path.startswith('//'):
		messages.info(
				request,
				f'This document is located at: {file_path}. Please access it from your network drive.'
				)
		return redirect('documents:document_detail', pk=document.pk)
	
	# Check if it's a URL
	if file_path.startswith('http://') or file_path.startswith('https://'):
		# Track download
		track_document_download(request, document)
		return redirect(file_path)
	
	# Try to serve local file
	if os.path.exists(file_path):
		return serve_local_file(request, document, file_path)
	
	messages.error(request, f"File not found at: {file_path}")
	return redirect('documents:document_detail', pk=document.pk)


def serve_local_file(request, document, file_path):
	"""
	Serve a file from a local path.
	"""
	file_size = os.path.getsize(file_path)
	file_name = os.path.basename(file_path)
	content_type = get_content_type(file_path)
	
	try:
		response = FileResponse(
				open(file_path, 'rb'),
				content_type=content_type,
				as_attachment=True,
				filename=file_name
				)
		response['Content-Length'] = file_size
		
		track_document_download(request, document)
		
		return response
	
	except PermissionError:
		messages.error(request, "Permission denied. Unable to access the file.")
		return redirect('documents:document_detail', pk=document.pk)
	except Exception as e:
		messages.error(request, f"Error accessing file: {str(e)}")
		return redirect('documents:document_detail', pk=document.pk)


def get_content_type(file_path):
	"""
	Determine the content type of a file based on its extension.
	"""
	content_type, encoding = mimetypes.guess_type(file_path)
	
	if content_type is None:
		# Default to binary for unknown types
		content_type = 'application/octet-stream'
	
	# Special handling for common engineering file types
	extension_map = {
			'.dwg': 'application/acad',
			'.dxf': 'application/dxf',
			'.rvt': 'application/octet-stream',
			'.rfa': 'application/octet-stream',
			'.nwd': 'application/octet-stream',
			'.ifc': 'application/octet-stream',
			}
	
	ext = os.path.splitext(file_path)[1].lower()
	if ext in extension_map:
		content_type = extension_map[ext]
	
	return content_type


# def track_document_download(request, document):
# 	"""
# 	Track document download activity.
# 	Can be extended to log downloads, send notifications, etc.
# 	"""
# 	# Update download count (if you add this field to Document model)
# 	# document.download_count += 1
# 	# document.last_downloaded = timezone.now()
# 	# document.save(update_fields=['download_count', 'last_downloaded'])
#
# 	# Log download activity (if you have an activity log model)
# 	# DocumentActivity.objects.create(
# 	#     document=document,
# 	#     user=request.user,
# 	#     activity_type='DOWNLOAD',
# 	#     description=f'Document downloaded by {request.user.get_full_name()}',
# 	#     ip_address=get_client_ip(request)
# 	# )
	
	# pass
def track_document_download(request, document):
	"""Track document download activity."""
	DocumentDownload.objects.create(
			document=document,
			user=request.user,
			ip_address=get_client_ip(request),
			user_agent=request.META.get('HTTP_USER_AGENT', ''),
			file_size=document.file_upload.size if document.file_upload else None
			)

def get_client_ip(request):
	"""Get client IP address from request."""
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0]
	else:
		ip = request.META.get('REMOTE_ADDR')
	return ip


def document_preview_view(request, pk):
	"""
	Preview a document in the browser (inline) instead of downloading.
	Useful for PDFs and images.
	"""
	document = get_object_or_404(Document, pk=pk)
	
	# Check permissions
	if not can_user_download_document(request.user, document):
		messages.error(request, "You don't have permission to preview this document.")
		return redirect('documents:document_detail', pk=document.pk)
	
	if not document.file_upload:
		messages.error(request, "No file available for preview.")
		return redirect('documents:document_detail', pk=document.pk)
	
	file_path = document.file_upload.path
	
	if not os.path.exists(file_path):
		messages.error(request, "File not found on server.")
		return redirect('documents:document_detail', pk=document.pk)
	
	content_type = get_content_type(file_path)
	
	# Only allow preview for certain file types
	preview_types = [
			'application/pdf',
			'image/jpeg',
			'image/png',
			'image/gif',
			'image/bmp',
			'image/tiff',
			'image/webp',
			'text/plain',
			'text/csv',
			]
	
	if content_type not in preview_types:
		# Fall back to download for non-previewable files
		return download_uploaded_file(request, document)
	
	try:
		response = FileResponse(
				open(file_path, 'rb'),
				content_type=content_type
				)
		
		# Display inline instead of downloading
		response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
		
		return response
	
	except Exception as e:
		messages.error(request, f"Error previewing file: {str(e)}")
		return redirect('documents:document_detail', pk=document.pk)


def document_download_multiple_view(request):
	"""
	Download multiple documents as a ZIP file.
	"""
	import zipfile
	import tempfile
	from io import BytesIO
	
	document_ids = request.GET.getlist('documents') or request.POST.getlist('documents')
	
	if not document_ids:
		messages.error(request, "No documents selected for download.")
		return redirect('documents:document_list')
	
	documents = Document.objects.filter(pk__in=document_ids)
	
	# Filter documents user can access
	accessible_documents = []
	for doc in documents:
		if can_user_download_document(request.user, doc):
			accessible_documents.append(doc)
	
	if not accessible_documents:
		messages.error(request, "You don't have permission to download any of the selected documents.")
		return redirect('documents:document_list')
	
	# Create ZIP file in memory
	zip_buffer = BytesIO()
	
	with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
		for doc in accessible_documents:
			if doc.file_upload and os.path.exists(doc.file_upload.path):
				# Add file to ZIP
				file_name = f"{doc.document_number}_{os.path.basename(doc.file_upload.path)}"
				zip_file.write(doc.file_upload.path, file_name)
	
	# Prepare response
	zip_buffer.seek(0)
	
	timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
	zip_filename = f"documents_{timestamp}.zip"
	
	response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
	response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
	response['Content-Length'] = zip_buffer.getbuffer().nbytes
	
	return response


def document_version_download_view(request, pk, revision_pk):
	"""
	Download a specific revision of a document.
	"""
	document = get_object_or_404(Document, pk=pk)
	revision = get_object_or_404(Document, pk=revision_pk, document_number=document.document_number)
	
	if not can_user_download_document(request.user, revision):
		messages.error(request, "You don't have permission to download this revision.")
		return redirect('documents:document_detail', pk=document.pk)
	
	if revision.file_upload:
		return download_uploaded_file(request, revision)
	
	messages.error(request, "No file attached to this revision.")
	return redirect('documents:document_detail', pk=document.pk)