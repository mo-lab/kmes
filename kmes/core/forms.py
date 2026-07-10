# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Project, Area, System, EquipmentTag


DATE_INPUT = forms.DateInput(attrs={'class': 'form-control','type': 'date'})


class ProjectForm(forms.ModelForm):
	class Meta:
		model = Project
		fields = [
				'name', 'code', 'location', 'description',
				'start_date', 'target_completion_date', 'actual_completion_date',
				'status',
				]
		widgets = {
				'description': forms.Textarea(attrs={'rows': 4}),
				'start_date': DATE_INPUT,
				'target_completion_date': DATE_INPUT,
				'actual_completion_date': DATE_INPUT,
				'status': forms.Select(attrs={
						'class': 'form-select'
						}),
				}
		help_texts = {
				'code': _("Short code, e.g., 'CU-PH2'"),
				}
	
	def clean(self):
		cleaned = super().clean()
		start = cleaned.get('start_date')
		target = cleaned.get('target_completion_date')
		actual = cleaned.get('actual_completion_date')
		
		if start and target and target < start:
			raise ValidationError({
					'target_completion_date': _("Target completion date cannot be before start date.")
					})
		
		if start and actual and actual < start:
			raise ValidationError({
					'actual_completion_date': _("Actual completion date cannot be before start date.")
					})
		
		return cleaned


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
	class Meta:
		model = System
		fields = ['project', 'code', 'name', 'description']
		widgets = {
				'description': forms.Textarea(attrs={'rows': 3}),
				}
	
	def clean(self):
		cleaned = super().clean()
		project = cleaned.get('project')
		code = cleaned.get('code')
		
		if project and code:
			qs = System.objects.filter(project=project, code=code)
			if self.instance.pk:
				qs = qs.exclude(pk=self.instance.pk)
			if qs.exists():
				raise ValidationError({
						'code': _("A system with this code already exists for the selected project.")
						})
		return cleaned


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
			