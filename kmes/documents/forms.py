from django import forms
from .models import Document, DocumentShare, User,TagDocument


class DocumentForm(forms.ModelForm):
	"""Form for creating and updating documents."""
	
	# Make document_number not required
	document_number = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control',
					'placeholder': 'Auto-generated if left blank'
					})
			)
	
	class Meta:
		model = Document
		fields = [
				'project', 'document_number', 'title', 'doc_type',
				'discipline', 'revision', 'status', 'file_upload',
				'file_path', 'issue_date', 'notes'
				]
		widgets = {
				'project': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'title': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., HPGR Foundation Drawing',
						'required': 'required'
						}),
				'doc_type': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'discipline': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'revision': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., A, B, C or 0, 1, 2',
						'required': 'required'
						}),
				'status': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'file_upload': forms.FileInput(attrs={
						'class': 'form-control'
						}),
				'file_path': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': '/network/path/to/document.pdf'
						}),
				'issue_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'notes': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 3,
						'placeholder': 'Additional notes about this document...'
						}),
				}
	
	def clean(self):
		cleaned_data = super().clean()
		file_upload = cleaned_data.get('file_upload')
		file_path = cleaned_data.get('file_path')
		status = cleaned_data.get('status')
		issue_date = cleaned_data.get('issue_date')
		
		# Require file for new documents
		if not self.instance.pk and not file_upload and not file_path:
			raise forms.ValidationError(
					"Please either upload a file or provide a file path."
					)
		
		# Require issue date for approved/IFC documents
		if status in ['APPR', 'IFC', 'ASBL'] and not issue_date:
			self.add_error('issue_date', 'Issue date is required for approved/IFC documents.')
		
		return cleaned_data
	
	def clean_document_number(self):
		document_number = self.cleaned_data.get('document_number')
		
		# If document number is empty, generate one
		if not document_number:
			project = self.cleaned_data.get('project')
			doc_type = self.cleaned_data.get('doc_type', 'OTHR')
			discipline = self.cleaned_data.get('discipline', 'GEN')
			
			if project:
				document_number = self.generate_document_number(project, doc_type, discipline)
			else:
				raise forms.ValidationError("Project is required to generate document number.")
		
		# Check for uniqueness
		if Document.objects.filter(document_number=document_number).exists():
			if not self.instance.pk or Document.objects.filter(document_number=document_number).exclude(pk=self.instance.pk).exists():
				raise forms.ValidationError(
						f"Document number '{document_number}' already exists. Please use a different number."
						)
		
		return document_number
	
	def generate_document_number(self, project, doc_type, discipline):
		"""Generate a unique document number."""
		from django.utils import timezone
		
		# Get project code
		project_code = project.code if project else 'GEN'
		
		# Get current date
		now = timezone.now()
		date_str = now.strftime('%y%m%d')
		
		# Count existing documents for this project
		count = Document.objects.filter(project=project).count() + 1
		
		# Format: PRJ-TYPE-DISC-YYMMDD-NNNN
		return f"{project_code}-{doc_type}-{discipline}-{date_str}-{count:04d}"

class DocumentShareForm(forms.Form):
	"""Form for sharing documents with users."""
	
	users = forms.ModelMultipleChoiceField(
			queryset=User.objects.filter(is_active=True),
			widget=forms.SelectMultiple(attrs={
					'class': 'form-select',
					'size': '8'
					}),
			help_text="Select users to share this document with"
			)
	can_edit = forms.BooleanField(
			required=False,
			initial=False,
			widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
			help_text="Allow recipients to edit this document"
			)
	message = forms.CharField(
			required=False,
			widget=forms.Textarea(attrs={
					'class': 'form-control',
					'rows': 3,
					'placeholder': 'Optional message to recipients...'
					})
			)
	
	def __init__(self, *args, **kwargs):
		self.document = kwargs.pop('document', None)
		self.user = kwargs.pop('user', None)
		super().__init__(*args, **kwargs)
		
		# Exclude users who already have access
		if self.document:
			already_shared = DocumentShare.objects.filter(
					document=self.document
					).values_list('shared_with_id', flat=True)
			
			# Also exclude the document owner/submitter
			exclude_ids = list(already_shared)
			if self.document.submitted_by:
				exclude_ids.append(self.document.submitted_by_id)
			if self.user:
				exclude_ids.append(self.user.id)
			
			self.fields['users'].queryset = User.objects.filter(
					is_active=True
					).exclude(id__in=exclude_ids)


class DocumentShareUpdateForm(forms.ModelForm):
	"""Form for updating share permissions."""
	
	class Meta:
		model = DocumentShare
		fields = ['can_edit', 'message']
		widgets = {
				'can_edit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
				'message': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 2
						}),
				}


class TagDocumentForm(forms.ModelForm):
	"""Form for linking documents to equipment tags."""
	
	class Meta:
		model = TagDocument
		fields = ['equipment_tag', 'document', 'relation_type']
		widgets = {
				'equipment_tag': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'document': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'relation_type': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., \'references\',defines, specifies'
						}),
				}
	
	def __init__(self, *args, **kwargs):
		project_id = kwargs.pop('project_id', None)
		super().__init__(*args, **kwargs)
		
		if project_id:
			try:
				from core.models import EquipmentTag
				self.fields['equipment_tag'].queryset = EquipmentTag.objects.filter(
						project_id=project_id
						)
			except ImportError:
				pass
			
			self.fields['document'].queryset = Document.objects.filter(
					project_id=project_id
					)
	
	def clean(self):
		cleaned_data = super().clean()
		equipment_tag = cleaned_data.get('equipment_tag')
		document = cleaned_data.get('document')
		
		# if equipment_tag and document:
		# 	# Check if they belong to the same project
		# 	if equipment_tag.project_id != document.project_id:
		# 		raise forms.ValidationError(
		# 				"Equipment tag and document must belong to the same project."
		# 				)
		
		return cleaned_data


class DocumentSearchForm(forms.Form):
	"""Form for searching and filtering documents in the list view."""
	
	project = forms.CharField(
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	doc_type = forms.ChoiceField(
			choices=[('', 'All Types')] + list(Document.DocType.choices),
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	discipline = forms.ChoiceField(
			choices=[('', 'All Disciplines')] + list(Document.Discipline.choices),
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	status = forms.ChoiceField(
			choices=[('', 'All Statuses')] + list(Document.DocStatus.choices),
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	search = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control form-control-sm',
					'placeholder': 'Search by document number, title, or tag...',
					'aria-label': 'Search documents'
					})
			)
	
	date_from = forms.DateField(
			required=False,
			widget=forms.DateInput(attrs={
					'class': 'form-control form-control-sm',
					'type': 'date',
					'placeholder': 'From date',
					'onchange': 'this.form.submit()'
					})
			)
	
	date_to = forms.DateField(
			required=False,
			widget=forms.DateInput(attrs={
					'class': 'form-control form-control-sm',
					'type': 'date',
					'placeholder': 'To date',
					'onchange': 'this.form.submit()'
					})
			)
	
	has_file = forms.BooleanField(
			required=False,
			widget=forms.CheckboxInput(attrs={
					'class': 'form-check-input',
					'onchange': 'this.form.submit()'
					})
			)
	
	def clean(self):
		cleaned_data = super().clean()
		
		# Validate date range
		date_from = cleaned_data.get('date_from')
		date_to = cleaned_data.get('date_to')
		
		if date_from and date_to and date_from > date_to:
			self.add_error('date_to', 'End date must be after start date.')
		
		return cleaned_data
	
	def apply_filters(self, queryset):
		"""Apply form filters to a queryset."""
		if not self.is_valid():
			return queryset
		
		data = self.cleaned_data
		
		if data.get('project'):
			queryset = queryset.filter(project_id=data['project'])
		
		if data.get('doc_type'):
			queryset = queryset.filter(doc_type=data['doc_type'])
		
		if data.get('discipline'):
			queryset = queryset.filter(discipline=data['discipline'])
		
		if data.get('status'):
			queryset = queryset.filter(status=data['status'])
		
		if data.get('search'):
			from django.db.models import Q
			search = data['search']
			queryset = queryset.filter(
					Q(document_number__icontains=search) |
					Q(title__icontains=search) |
					Q(notes__icontains=search)
					).distinct()
		
		if data.get('date_from'):
			queryset = queryset.filter(created_at__date__gte=data['date_from'])
		
		if data.get('date_to'):
			queryset = queryset.filter(created_at__date__lte=data['date_to'])
		
		if data.get('has_file'):
			queryset = queryset.filter(file_upload__isnull=False)
		
		return queryset
	
class TagDocumentBulkForm(forms.Form):
	"""Form for bulk linking documents and tags."""
	
	MODE_CHOICES = [
			('tags_to_document', 'Link One Document to Multiple Tags'),
			('documents_to_tag', 'Link Multiple Documents to One Tag'),
			]
	
	RELATION_TYPE_CHOICES = [
			('references', 'References'),
			('defines', 'Defines'),
			('specifies', 'Specifies'),
			('illustrates', 'Illustrates'),
			('supports', 'Supports'),
			]
	
	mode = forms.ChoiceField(
			choices=MODE_CHOICES,
			widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
			initial='documents_to_tag'
			)
	
	# For mode: documents_to_tag
	equipment_tag = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control',
					'placeholder': 'Search and select a tag...',
					'id': 'tagSearch'
					})
			)
	equipment_tag_id = forms.IntegerField(
			required=False,
			widget=forms.HiddenInput(attrs={'id': 'tagId'})
			)
	documents = forms.ModelMultipleChoiceField(
			queryset=Document.objects.all(),
			required=False,
			widget=forms.SelectMultiple(attrs={
					'class': 'form-select',
					'size': '10'
					})
			)
	
	# For mode: tags_to_document
	document = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control',
					'placeholder': 'Search and select a document...',
					'id': 'documentSearch'
					})
			)
	document_id = forms.IntegerField(
			required=False,
			widget=forms.HiddenInput(attrs={'id': 'documentId'})
			)
	equipment_tags = forms.ModelMultipleChoiceField(
			queryset=None,  # Set in __init__
			required=False,
			widget=forms.SelectMultiple(attrs={
					'class': 'form-select',
					'size': '10'
					})
			)
	
	relation_type = forms.ChoiceField(
			choices=RELATION_TYPE_CHOICES,
			initial='references',
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	
	def __init__(self, *args, **kwargs):
		project_id = kwargs.pop('project_id', None)
		super().__init__(*args, **kwargs)
		
		try:
			from core.models import EquipmentTag
			if project_id:
				self.fields['equipment_tags'].queryset = EquipmentTag.objects.filter(
						project_id=project_id
						)
				self.fields['documents'].queryset = Document.objects.filter(
						project_id=project_id
						)
			else:
				self.fields['equipment_tags'].queryset = EquipmentTag.objects.all()
				self.fields['documents'].queryset = Document.objects.all()
		except ImportError:
			self.fields['equipment_tags'].queryset = None
	
	def clean(self):
		cleaned_data = super().clean()
		mode = cleaned_data.get('mode')
		
		if mode == 'documents_to_tag':
			tag_id = cleaned_data.get('equipment_tag_id')
			if not tag_id:
				self.add_error('equipment_tag', 'Please select an equipment tag.')
			
			documents = cleaned_data.get('documents')
			if not documents:
				self.add_error('documents', 'Please select at least one document.')
		
		elif mode == 'tags_to_document':
			doc_id = cleaned_data.get('document_id')
			if not doc_id:
				self.add_error('document', 'Please select a document.')
			
			tags = cleaned_data.get('equipment_tags')
			if not tags:
				self.add_error('equipment_tags', 'Please select at least one tag.')
		
		return cleaned_data