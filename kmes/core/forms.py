from django import forms
from django.core.exceptions import ValidationError
from models import Project, Area, System, EquipmentTag


class ProjectForm(forms.ModelForm):
	"""Form for creating and updating projects."""
	
	class Meta:
		model = Project
		fields = [
				'name', 'code', 'location', 'description',
				'start_date', 'target_completion_date', 'status'
				]
		widgets = {
				'name': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., Copper Mine Phase 2 Expansion'
						}),
				'code': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., CU-PH2'
						}),
				'location': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., Site A, Chile'
						}),
				'description': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 4,
						'placeholder': 'Brief description of the project scope...'
						}),
				'start_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'target_completion_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'status': forms.Select(attrs={'class': 'form-select'}),
				}
	
	def clean(self):
		cleaned_data = super().clean()
		start_date = cleaned_data.get('start_date')
		target_completion_date = cleaned_data.get('target_completion_date')
		
		if start_date and target_completion_date:
			if target_completion_date < start_date:
				raise ValidationError(
						"Target completion date cannot be before start date."
						)
		return cleaned_data


class AreaForm(forms.ModelForm):
	"""Form for creating and updating areas."""
	
	class Meta:
		model = Area
		fields = ['project', 'code', 'name', 'description']
		widgets = {
				'project': forms.Select(attrs={'class': 'form-select'}),
				'code': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., AREA-100'
						}),
				'name': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., Primary Crushing Station'
						}),
				'description': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 3,
						'placeholder': 'Describe this area...'
						}),
				}


class SystemForm(forms.ModelForm):
	"""Form for creating and updating systems."""
	
	class Meta:
		model = System
		fields = ['project', 'code', 'name', 'description']
		widgets = {
				'project': forms.Select(attrs={'class': 'form-select'}),
				'code': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., SYS-LUBE-HPGR'
						}),
				'name': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., HPGR Lubrication System'
						}),
				'description': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 3,
						'placeholder': 'Describe this system...'
						}),
				}


class EquipmentTagForm(forms.ModelForm):
	"""Form for creating and updating equipment tags."""
	
	class Meta:
		model = EquipmentTag
		fields = [
				'project', 'area', 'system', 'parent_tag',
				'tag_number', 'description', 'equipment_type',
				'discipline', 'manufacturer', 'model_number',
				'serial_number', 'criticality', 'status',
				'installation_date', 'weight_kg', 'dimensions', 'notes'
				]
		widgets = {
				'project': forms.Select(attrs={'class': 'form-select'}),
				'area': forms.Select(attrs={'class': 'form-select'}),
				'system': forms.Select(attrs={'class': 'form-select'}),
				'parent_tag': forms.Select(attrs={'class': 'form-select'}),
				'tag_number': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., HPGR-001'
						}),
				'description': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., High-Pressure Grinding Roll'
						}),
				'equipment_type': forms.Select(attrs={'class': 'form-select'}),
				'discipline': forms.Select(attrs={'class': 'form-select'}),
				'manufacturer': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., Metso, FLSmidth'
						}),
				'model_number': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., HRC 3000'
						}),
				'serial_number': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'Enter serial number'
						}),
				'criticality': forms.Select(attrs={'class': 'form-select'}),
				'status': forms.Select(attrs={'class': 'form-select'}),
				'installation_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'weight_kg': forms.NumberInput(attrs={
						'class': 'form-control',
						'placeholder': 'Weight in kilograms'
						}),
				'dimensions': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': "LxWxH in mm, e.g., '3000x2000x1500'"
						}),
				'notes': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 3,
						'placeholder': 'Additional notes...'
						}),
				}
	
	def __init__(self, *args, **kwargs):
		project_id = kwargs.pop('project_id', None)
		super().__init__(*args, **kwargs)
		
		# If project is provided, filter dependent dropdowns
		if project_id:
			self.fields['area'].queryset = Area.objects.filter(project_id=project_id)
			self.fields['system'].queryset = System.objects.filter(project_id=project_id)
			self.fields['parent_tag'].queryset = EquipmentTag.objects.filter(
					project_id=project_id
					)
		elif self.instance.pk and self.instance.project_id:
			self.fields['area'].queryset = Area.objects.filter(
					project_id=self.instance.project_id
					)
			self.fields['system'].queryset = System.objects.filter(
					project_id=self.instance.project_id
					)
			# Exclude self and descendants to prevent circular references
			descendants = self.instance.child_tags.all().values_list('id', flat=True)
			self.fields['parent_tag'].queryset = EquipmentTag.objects.filter(
					project_id=self.instance.project_id
					).exclude(id__in=[self.instance.id] + list(descendants))
		else:
			self.fields['area'].queryset = Area.objects.none()
			self.fields['system'].queryset = System.objects.none()
			self.fields['parent_tag'].queryset = EquipmentTag.objects.none()
	
	def clean_parent_tag(self):
		parent_tag = self.cleaned_data.get('parent_tag')
		if parent_tag and self.instance.pk:
			# Check for circular reference
			current = parent_tag
			while current:
				if current == self.instance:
					raise ValidationError(
							"Cannot set a descendant as parent tag (circular reference)."
							)
				current = current.parent_tag
		return parent_tag


class EquipmentTagFilterForm(forms.Form):
	"""Form for filtering equipment tags in lists."""
	
	project = forms.ModelChoiceField(
			queryset=Project.objects.all(),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	area = forms.ModelChoiceField(
			queryset=Area.objects.none(),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	equipment_type = forms.ChoiceField(
			choices=[('', 'All Types')] + list(EquipmentTag.EquipmentType.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	status = forms.ChoiceField(
			choices=[('', 'All Statuses')] + list(EquipmentTag.Status.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	discipline = forms.ChoiceField(
			choices=[('', 'All Disciplines')] + list(EquipmentTag.Discipline.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	criticality = forms.ChoiceField(
			choices=[('', 'All Criticalities')] + list(EquipmentTag.Criticality.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	search = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control',
					'placeholder': 'Search by tag number or description...'
					})
			)
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if 'project' in self.data:
			try:
				project_id = int(self.data.get('project'))
				self.fields['area'].queryset = Area.objects.filter(project_id=project_id)
			except (ValueError, TypeError):
				pass


class EquipmentTagBulkUpdateForm(forms.Form):
	"""Form for bulk updating equipment tags."""
	
	tag_ids = forms.CharField(
			widget=forms.HiddenInput(),
			help_text="Comma-separated list of tag IDs"
			)
	status = forms.ChoiceField(
			choices=[('', '--- Keep Current ---')] + list(EquipmentTag.Status.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	area = forms.ModelChoiceField(
			queryset=Area.objects.all(),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	criticality = forms.ChoiceField(
			choices=[('', '--- Keep Current ---')] + list(EquipmentTag.Criticality.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	installation_date = forms.DateField(
			required=False,
			widget=forms.DateInput(attrs={
					'class': 'form-control',
					'type': 'date'
					})
			)
	
	def clean_tag_ids(self):
		tag_ids = self.cleaned_data['tag_ids']
		try:
			return [int(id.strip()) for id in tag_ids.split(',') if id.strip()]
		except ValueError:
			raise ValidationError("Invalid tag IDs format.")


class EquipmentTagHierarchyMoveForm(forms.Form):
	"""Form for moving a tag in the hierarchy."""
	
	new_parent_tag = forms.ModelChoiceField(
			queryset=EquipmentTag.objects.all(),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'}),
			help_text="Select new parent tag (leave empty for top level)"
			)
	
	def __init__(self, *args, **kwargs):
		self.tag = kwargs.pop('tag', None)
		super().__init__(*args, **kwargs)
		
		if self.tag:
			# Exclude self and all descendants from possible parents
			descendants = self.tag.child_tags.all().values_list('id', flat=True)
			self.fields['new_parent_tag'].queryset = EquipmentTag.objects.filter(
					project_id=self.tag.project_id
					).exclude(id__in=[self.tag.id] + list(descendants))