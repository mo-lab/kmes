from django import forms
from .models import Document, DocumentShare, User


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