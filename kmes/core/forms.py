# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Project, Area, System, EquipmentTag


DATE_INPUT = forms.DateInput(attrs={'class': 'form-control','type': 'date'})


class ProjectForm(forms.ModelForm):
	"""Form for creating and updating projects."""
	
	class Meta:
		model = Project
		fields = [
				'name', 'code', 'location', 'description',
				'start_date', 'target_completion_date', 'actual_completion_date',
				'status'
				]
		widgets = {
				'name': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., Copper Mine Phase 2 Expansion',
						'required': 'required'
						}),
				'code': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'Auto-generated if left blank',
						}),
				'location': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., Site A, Antofagasta, Chile',
						'required': 'required'
						}),
				'description': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 4,
						'placeholder': 'Brief description of the project scope, objectives, and key deliverables...'
						}),
				'start_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date',
						'required': 'required'
						}),
				'target_completion_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date',
						'required': 'required'
						}),
				'actual_completion_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'status': forms.HiddenInput(),
				}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['actual_completion_date'].required = False
	
	def clean(self):
		cleaned_data = super().clean()
		start_date = cleaned_data.get('start_date')
		target_completion_date = cleaned_data.get('target_completion_date')
		actual_completion_date = cleaned_data.get('actual_completion_date')
		
		if start_date and target_completion_date and target_completion_date < start_date:
			self.add_error('target_completion_date', 'Target completion date cannot be before start date.')
		
		if actual_completion_date and start_date and actual_completion_date < start_date:
			self.add_error('actual_completion_date', 'Actual completion date cannot be before start date.')
		
		return cleaned_data
	
	def clean_code(self):
		code = self.cleaned_data.get('code')
		if code:
			# Check uniqueness
			qs = Project.objects.filter(code=code)
			if self.instance.pk:
				qs = qs.exclude(pk=self.instance.pk)
			if qs.exists():
				raise forms.ValidationError('A project with this code already exists.')
		return code

class AreaForm(forms.ModelForm):
	class Meta:
		model = Area
		fields = ['project', 'code', 'name', 'description']
		widgets = {
				'description': forms.Textarea(attrs={'rows': 3}),
				}
	
	def clean(self):
		cleaned = super().clean()
		project = cleaned.get('project')
		code = cleaned.get('code')
		
		if project and code:
			qs = Area.objects.filter(project=project, code=code)
			if self.instance.pk:
				qs = qs.exclude(pk=self.instance.pk)
			if qs.exists():
				raise ValidationError({
						'code': _("An area with this code already exists for the selected project.")
						})
		return cleaned


class SystemForm(forms.ModelForm):
	"""Form for creating and updating systems."""
	
	class Meta:
		model = System
		fields = ['project', 'code', 'name', 'description']
		widgets = {
				'project': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'code': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'Auto-generated if left blank',
						}),
				'name': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., High-Pressure Grinding Roll Lubrication System',
						'required': 'required'
						}),
				'description': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 3,
						'placeholder': 'Describe the function and scope of this system...'
						}),
				}
	
	def __init__(self, *args, **kwargs):
		project_id = kwargs.pop('project_id', None)
		super().__init__(*args, **kwargs)
		
		if project_id:
			self.fields['project'].queryset = Project.objects.filter(pk=project_id)
			self.fields['project'].initial = project_id
	
	def clean_code(self):
		code = self.cleaned_data.get('code')
		project = self.cleaned_data.get('project')
		
		if code and project:
			# Check uniqueness within project
			qs = System.objects.filter(project=project, code=code)
			if self.instance.pk:
				qs = qs.exclude(pk=self.instance.pk)
			if qs.exists():
				raise forms.ValidationError('A system with this code already exists in this project.')
		
		return code

class EquipmentTagForm(forms.ModelForm):
	class Meta:
		model = EquipmentTag
		fields = [
				'project', 'area', 'system', 'parent_tag',
				'tag_number', 'description', 'equipment_type', 'discipline',
				'manufacturer', 'model_number', 'serial_number',
				'criticality', 'status',
				'installation_date', 'weight_kg', 'dimensions', 'notes',
				]
		widgets = {
				'description': forms.Textarea(attrs={'rows': 3}),
				'notes': forms.Textarea(attrs={'rows': 4}),
				'equipment_type': forms.Select(),
				'discipline': forms.Select(),
				'criticality': forms.Select(),
				'status': forms.Select(),
				'installation_date': DATE_INPUT,
				'weight_kg': forms.NumberInput(attrs={'step': '0.01'}),
				}
		help_texts = {
				'dimensions': _("LxWxH in mm, e.g., '3000x2000x1500'"),
				}
	
	def clean_parent_tag(self):
		parent = self.cleaned_data.get('parent_tag')
		project = self.cleaned_data.get('project')
		
		if parent:
			# Parent must belong to same project
			if parent.project_id != (project.id if project else None):
				raise ValidationError(_("Parent tag must belong to the same project."))
			
			# Prevent direct self-parenting
			if self.instance.pk and parent.pk == self.instance.pk:
				raise ValidationError(_("An equipment tag cannot be its own parent."))
			
			# Prevent cycles: walk up the parent chain
			ancestor = parent
			while ancestor is not None:
				if self.instance.pk and ancestor.pk == self.instance.pk:
					raise ValidationError(_("Selecting this parent would create a cycle in the hierarchy."))
				ancestor = ancestor.parent_tag
		
		return parent
	
	def clean_dimensions(self):
		dims = self.cleaned_data.get('dimensions', '').strip()
		if dims == '':
			return dims
		# Expect format like 3000x2000x1500 (three positive integers)
		parts = dims.split('x')
		if len(parts) != 3:
			raise ValidationError(_("Dimensions must be in LxWxH format with three values separated by 'x'."))
		try:
			nums = [int(p) for p in parts]
		except ValueError:
			raise ValidationError(_("Each dimension must be an integer (mm)."))
		if any(n <= 0 for n in nums):
			raise ValidationError(_("Dimensions must be positive integers."))
		# Normalize formatting (no spaces)
		return 'x'.join(str(n) for n in nums)
	
	def clean(self):
		cleaned = super().clean()
		project = cleaned.get('project')
		area = cleaned.get('area')
		system = cleaned.get('system')
		parent = cleaned.get('parent_tag')
		
		# If area or system provided, ensure they belong to the same project (if project provided)
		if project:
			if area and area.project_id != project.id:
				raise ValidationError({'area': _("Selected area does not belong to the chosen project.")})
			if system and system.project_id != project.id:
				raise ValidationError({'system': _("Selected system does not belong to the chosen project.")})
			if parent and parent.project_id != project.id:
				raise ValidationError({'parent_tag': _("Parent tag does not belong to the chosen project.")})
		
		# Ensure tag_number uniqueness within project (helpful UX; model-level indexes still enforce)
		tag_number = cleaned.get('tag_number')
		if project and tag_number:
			qs = EquipmentTag.objects.filter(project=project, tag_number=tag_number)
			if self.instance.pk:
				qs = qs.exclude(pk=self.instance.pk)
			if qs.exists():
				raise ValidationError({'tag_number': _("An equipment tag with this tag number already exists in the project.")})
		
		return cleaned
	
class EquipmentTagFilterForm(forms.Form):
	"""Form for filtering equipment tags in lists."""
	
	project = forms.ModelChoiceField(
			queryset=Project.objects.all(),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	area = forms.ModelChoiceField(
			queryset=Area.objects.none(),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	system = forms.ModelChoiceField(
			queryset=System.objects.none(),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	equipment_type = forms.ChoiceField(
			choices=[('', 'All Types')] + list(EquipmentTag.EquipmentType.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	status = forms.ChoiceField(
			choices=[('', 'All Statuses')] + list(EquipmentTag.Status.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	discipline = forms.ChoiceField(
			choices=[('', 'All Disciplines')] + list(EquipmentTag.Discipline.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	criticality = forms.ChoiceField(
			choices=[('', 'All Criticalities')] + list(EquipmentTag.Criticality.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	search = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control form-control-sm',
					'placeholder': 'Search tags...'
					})
			)
	parent_tag_only = forms.ChoiceField(
			choices=[('', 'All'), ('true', 'Top Level Only'), ('false', 'Children Only')],
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		# Filter areas based on selected project
		if 'project' in self.data:
			try:
				project_id = int(self.data.get('project'))
				self.fields['area'].queryset = Area.objects.filter(project_id=project_id)
				self.fields['system'].queryset = System.objects.filter(project_id=project_id)
			except (ValueError, TypeError):
				pass
		elif self.initial.get('project'):
			project_id = self.initial['project']
			self.fields['area'].queryset = Area.objects.filter(project_id=project_id)
			self.fields['system'].queryset = System.objects.filter(project_id=project_id)

from django import forms
from .models import EquipmentLocation, EquipmentLocationImage


class EquipmentLocationForm(forms.ModelForm):
	"""Form for recording equipment location."""
	
	class Meta:
		model = EquipmentLocation
		fields = [
				'equipment_tag', 'location_type', 'latitude', 'longitude',
				'elevation', 'accuracy', 'area', 'building', 'floor',
				'room', 'grid_reference', 'address', 'city', 'state',
				'country', 'postal_code', 'is_current', 'arrival_date',
				'notes'
				]
		widgets = {
				'equipment_tag': forms.Select(attrs={'class': 'form-select'}),
				'location_type': forms.Select(attrs={'class': 'form-select'}),
				'latitude': forms.NumberInput(attrs={
						'class': 'form-control',
						'step': '0.000001',
						'placeholder': 'e.g., -23.550520'
						}),
				'longitude': forms.NumberInput(attrs={
						'class': 'form-control',
						'step': '0.000001',
						'placeholder': 'e.g., -46.633308'
						}),
				'elevation': forms.NumberInput(attrs={
						'class': 'form-control',
						'step': '0.01',
						'placeholder': 'Meters above sea level'
						}),
				'accuracy': forms.NumberInput(attrs={
						'class': 'form-control',
						'step': '0.01',
						'placeholder': 'GPS accuracy in meters'
						}),
				'area': forms.Select(attrs={'class': 'form-select'}),
				'building': forms.TextInput(attrs={'class': 'form-control'}),
				'floor': forms.TextInput(attrs={'class': 'form-control'}),
				'room': forms.TextInput(attrs={'class': 'form-control'}),
				'grid_reference': forms.TextInput(attrs={'class': 'form-control'}),
				'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
				'city': forms.TextInput(attrs={'class': 'form-control'}),
				'state': forms.TextInput(attrs={'class': 'form-control'}),
				'country': forms.TextInput(attrs={'class': 'form-control'}),
				'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
				'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
				'arrival_date': forms.DateTimeInput(attrs={
						'class': 'form-control',
						'type': 'datetime-local'
						}),
				'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
				}
	
	def __init__(self, *args, **kwargs):
		tag_id = kwargs.pop('tag_id', None)
		super().__init__(*args, **kwargs)
		
		if tag_id:
			self.fields['equipment_tag'].initial = tag_id
			self.fields['equipment_tag'].widget = forms.HiddenInput()
			self.fields['equipment_tag'].required = False
	
	def clean(self):
		cleaned_data = super().clean()
		latitude = cleaned_data.get('latitude')
		longitude = cleaned_data.get('longitude')
		
		if latitude and longitude:
			if latitude < -90 or latitude > 90:
				self.add_error('latitude', 'Latitude must be between -90 and 90 degrees.')
			if longitude < -180 or longitude > 180:
				self.add_error('longitude', 'Longitude must be between -180 and 180 degrees.')
		
		return cleaned_data


class EquipmentLocationImageForm(forms.ModelForm):
	"""Form for uploading location images."""
	
	class Meta:
		model = EquipmentLocationImage
		fields = [
				'image', 'title', 'description', 'image_type',
				'taken_date', 'direction', 'is_primary'
				]
		widgets = {
				'image': forms.FileInput(attrs={
						'class': 'form-control',
						'accept': 'image/*'
						}),
				'title': forms.TextInput(attrs={'class': 'form-control'}),
				'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
				'image_type': forms.Select(attrs={'class': 'form-select'}),
				'taken_date': forms.DateTimeInput(attrs={
						'class': 'form-control',
						'type': 'datetime-local'
						}),
				'direction': forms.NumberInput(attrs={
						'class': 'form-control',
						'min': '0',
						'max': '360',
						'step': '0.1'
						}),
				'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
				}


class EquipmentLocationSearchForm(forms.Form):
	"""Form for searching equipment locations."""
	
	equipment_tag = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control',
					'placeholder': 'Search by tag number...'
					})
			)
	location_type = forms.ChoiceField(
			choices=[('', 'All Types')] + list(EquipmentLocation.LocationType.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	is_current = forms.ChoiceField(
			choices=[('', 'All'), ('true', 'Current Only'), ('false', 'History Only')],
			required=False,
			widget=forms.Select(attrs={'class': 'form-select'})
			)
	date_from = forms.DateField(
			required=False,
			widget=forms.DateInput(attrs={
					'class': 'form-control',
					'type': 'date'
					})
			)
	date_to = forms.DateField(
			required=False,
			widget=forms.DateInput(attrs={
					'class': 'form-control',
					'type': 'date'
					})
			)


class SystemSearchForm(forms.Form):
	"""Form for searching and filtering systems."""
	
	project = forms.CharField(
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
					'placeholder': 'Search by code, name, description...'
					})
			)
	
	has_commissioning = forms.ChoiceField(
			choices=[('', 'All'), ('true', 'In Commissioning Only')],
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	commissioning_status = forms.ChoiceField(
			choices=[
					('', 'All Statuses'),
					('PREC', 'Pre-Commissioning'),
					('COLD', 'Cold Commissioning'),
					('HOT', 'Hot Commissioning'),
					('RAMP', 'Ramp-Up'),
					('PERF', 'Performance Test'),
					('HNDO', 'Handed Over'),
					],
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	has_defects = forms.ChoiceField(
			choices=[('', 'All'), ('true', 'Has Defects Only')],
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)