from django import forms
from models import Document, TagDocument
from ..core.models import EquipmentTag, Project


class DocumentForm(forms.ModelForm):
	"""Form for creating and updating documents."""
	
	class Meta:
		model = Document
		fields = [
				'project', 'document_number', 'title', 'doc_type',
				'discipline', 'revision', 'status', 'file_upload',
				'file_path', 'issue_date', 'notes'
				]
		widgets = {
				'project':         forms.Select(attrs={'class': 'form-select'}),
				'document_number': forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'e.g., DWG-1234-001'
								}
						),
				'title':           forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'e.g., HPGR Foundation Drawing'
								}
						),
				'doc_type':        forms.Select(attrs={'class': 'form-select'}),
				'discipline':      forms.Select(attrs={'class': 'form-select'}),
				'revision':        forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'e.g., Rev B, IFC'
								}
						),
				'status':          forms.Select(attrs={'class': 'form-select'}),
				'file_upload':     forms.FileInput(attrs={'class': 'form-control'}),
				'file_path':       forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': '/path/to/document.pdf'
								}
						),
				'issue_date':      forms.DateInput(
						attrs={
								'class': 'form-control',
								'type':  'date'
								}
						),
				'notes':           forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        3,
								'placeholder': 'Additional notes...'
								}
						),
				}
	
	def clean(self):
		cleaned_data = super().clean()
		file_upload = cleaned_data.get('file_upload')
		file_path = cleaned_data.get('file_path')
		
		if not file_upload and not file_path and not self.instance.pk:
			raise forms.ValidationError(
					"Please either upload a file or provide a file path."
					)
		return cleaned_data


class DocumentRevisionForm(forms.ModelForm):
	"""Specialized form for creating a new revision of a document."""
	
	class Meta:
		model = Document
		fields = ['revision', 'status', 'file_upload', 'notes']
		widgets = {
				'revision':    forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'e.g., Rev C'
								}
						),
				'status':      forms.Select(attrs={'class': 'form-select'}),
				'file_upload': forms.FileInput(attrs={'class': 'form-control'}),
				'notes':       forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        3,
								'placeholder': 'Describe changes in this revision...'
								}
						),
				}


class TagDocumentForm(forms.ModelForm):
	"""Form for linking documents to equipment tags."""
	
	class Meta:
		model = TagDocument
		fields = ['equipment_tag', 'document', 'relation_type']
		widgets = {
				'equipment_tag': forms.Select(attrs={'class': 'form-select'}),
				'document':      forms.Select(attrs={'class': 'form-select'}),
				'relation_type': forms.Select(attrs={'class': 'form-select'}),
				}
	
	def __init__(self, *args, **kwargs):
		project_id = kwargs.pop('project_id', None)
		super().__init__(*args, **kwargs)
		
		if project_id:
			self.fields['equipment_tag'].queryset = EquipmentTag.objects.filter(
					project_id=project_id
					)
			self.fields['document'].queryset = Document.objects.filter(
					project_id=project_id
					)


class DocumentSearchForm(forms.Form):
	"""Form for searching and filtering documents."""
	
	project = forms.ModelChoiceField(
			queryset=None,  # Set in __init__
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	doc_type = forms.ChoiceField(
			choices=[('', 'All Types')] + list(Document.DocType.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	discipline = forms.ChoiceField(
			choices=[('', 'All Disciplines')] + list(Document.Discipline.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	status = forms.ChoiceField(
			choices=[('', 'All Statuses')] + list(Document.DocStatus.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	search = forms.CharField(
			required=False,
			widget=forms.TextInput(
					attrs={
							'class':       'form-control',
							'placeholder': 'Search by document number or title...'
							}
					)
			)
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['project'].queryset = Project.objects.all()


class DocumentBulkUploadForm(forms.Form):
	"""Form for bulk uploading multiple documents."""
	
	project = forms.ModelChoiceField(
			queryset=None,  # Set in __init__
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	files = forms.FileField(
			widget=forms.ClearableFileInput(
					attrs={
							'class':    'form-control',
							'multiple': True
							}
					),
			help_text="Select multiple files to upload. File names will be used as document numbers."
			)
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.fields['project'].queryset = Project.objects.all()
