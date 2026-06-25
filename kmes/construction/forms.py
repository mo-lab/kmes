from django import forms
from ..construction.models import (
	WorkPackage, WorkPackageItem, DailyProgressReport,
	InstalledItemCheck, InstallationCheckPhoto
	)
from ..core.models import EquipmentTag


class WorkPackageForm(forms.ModelForm):
	"""Form for creating and updating work packages."""
	
	class Meta:
		model = WorkPackage
		fields = [
				'project', 'code', 'name', 'area', 'system',
				'description', 'supervisor', 'contractor',
				'planned_start', 'planned_finish', 'status',
				'priority', 'notes'
				]
		widgets = {
				'project': forms.Select(attrs={'class': 'form-select'}),
				'code': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., WP-CRUSH-INST-001'
						}),
				'name': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., Install HPGR and Feed Chute'
						}),
				'area': forms.Select(attrs={'class': 'form-select'}),
				'system': forms.Select(attrs={'class': 'form-select'}),
				'description': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 4,
						'placeholder': 'Detailed scope of work...'
						}),
				'supervisor': forms.Select(attrs={'class': 'form-select'}),
				'contractor': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., ABC Construction Ltd.'
						}),
				'planned_start': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'planned_finish': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'status': forms.Select(attrs={'class': 'form-select'}),
				'priority': forms.Select(attrs={'class': 'form-select'}),
				'notes': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 3,
						'placeholder': 'Additional notes...'
						}),
				}
	
	def clean(self):
		cleaned_data = super().clean()
		planned_start = cleaned_data.get('planned_start')
		planned_finish = cleaned_data.get('planned_finish')
		
		if planned_start and planned_finish and planned_finish < planned_start:
			raise forms.ValidationError(
					"Planned finish date cannot be before planned start date."
					)
		return cleaned_data


class WorkPackageItemForm(forms.ModelForm):
	"""Form for adding equipment tags to work packages."""
	
	class Meta:
		model = WorkPackageItem
		fields = ['equipment_tag', 'sequence_number', 'notes']
		widgets = {
				'equipment_tag': forms.Select(attrs={'class': 'form-select'}),
				'sequence_number': forms.NumberInput(attrs={
						'class': 'form-control',
						'min': '1'
						}),
				'notes': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 2,
						'placeholder': 'Installation notes...'
						}),
				}
	
	def __init__(self, *args, **kwargs):
		project_id = kwargs.pop('project_id', None)
		work_package_id = kwargs.pop('work_package_id', None)
		super().__init__(*args, **kwargs)
		
		if project_id:
			queryset = EquipmentTag.objects.filter(project_id=project_id)
			if work_package_id:
				# Exclude tags already in this work package
				existing_tag_ids = WorkPackageItem.objects.filter(
						work_package_id=work_package_id
						).values_list('equipment_tag_id', flat=True)
				queryset = queryset.exclude(id__in=existing_tag_ids)
			self.fields['equipment_tag'].queryset = queryset


class DailyProgressReportForm(forms.ModelForm):
	"""Form for daily progress reports."""
	
	class Meta:
		model = DailyProgressReport
		fields = [
				'work_package', 'report_date', 'work_performed_description',
				'issues_encountered', 'weather_conditions', 'temperature_celsius',
				'manpower_count', 'hours_worked'
				]
		widgets = {
				'work_package': forms.Select(attrs={'class': 'form-select'}),
				'report_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'work_performed_description': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 4,
						'placeholder': 'Describe work performed today...'
						}),
				'issues_encountered': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 3,
						'placeholder': 'Any issues, delays, or safety concerns...'
						}),
				'weather_conditions': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'e.g., Sunny, Cloudy, Rainy'
						}),
				'temperature_celsius': forms.NumberInput(attrs={
						'class': 'form-control',
						'placeholder': 'Temperature in °C'
						}),
				'manpower_count': forms.NumberInput(attrs={
						'class': 'form-control',
						'min': '0'
						}),
				'hours_worked': forms.NumberInput(attrs={
						'class': 'form-control',
						'min': '0',
						'step': '0.5'
						}),
				}


class InstalledItemCheckForm(forms.ModelForm):
	"""Form for installation quality checks."""
	
	class Meta:
		model = InstalledItemCheck
		fields = [
				'equipment_tag', 'checked_date',
				'foundation_ok', 'grouting_ok', 'bolting_ok',
				'alignment_ok', 'electrical_ok', 'status', 'comments'
				]
		widgets = {
				'equipment_tag': forms.Select(attrs={'class': 'form-select'}),
				'checked_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'foundation_ok': forms.Select(
						choices=[(None, '---'), (True, 'OK'), (False, 'Not OK')],
						attrs={'class': 'form-select'}
						),
				'grouting_ok': forms.Select(
						choices=[(None, '---'), (True, 'OK'), (False, 'Not OK')],
						attrs={'class': 'form-select'}
						),
				'bolting_ok': forms.Select(
						choices=[(None, '---'), (True, 'OK'), (False, 'Not OK')],
						attrs={'class': 'form-select'}
						),
				'alignment_ok': forms.Select(
						choices=[(None, '---'), (True, 'OK'), (False, 'Not OK')],
						attrs={'class': 'form-select'}
						),
				'electrical_ok': forms.Select(
						choices=[(None, '---'), (True, 'OK'), (False, 'Not OK')],
						attrs={'class': 'form-select'}
						),
				'status': forms.Select(attrs={'class': 'form-select'}),
				'comments': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 3,
						'placeholder': 'Inspection comments...'
						}),
				}
	
	def __init__(self, *args, **kwargs):
		project_id = kwargs.pop('project_id', None)
		super().__init__(*args, **kwargs)
		
		if project_id:
			self.fields['equipment_tag'].queryset = EquipmentTag.objects.filter(
					project_id=project_id,
					status__in=['INST', 'ALGN']  # Only installed or aligned tags
					)


class InstallationCheckPhotoForm(forms.ModelForm):
	"""Form for uploading photos to installation checks."""
	
	class Meta:
		model = InstallationCheckPhoto
		fields = ['photo', 'caption']
		widgets = {
				'photo': forms.FileInput(attrs={
						'class': 'form-control',
						'accept': 'image/*'
						}),
				'caption': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'Photo description'
						}),
				}


class WorkPackageProgressUpdateForm(forms.ModelForm):
	"""Simplified form for quick progress updates."""
	
	class Meta:
		model = WorkPackage
		fields = ['status', 'percent_complete', 'actual_start', 'actual_finish', 'notes']
		widgets = {
				'status': forms.Select(attrs={'class': 'form-select'}),
				'percent_complete': forms.NumberInput(attrs={
						'class': 'form-control',
						'min': '0',
						'max': '100',
						'step': '0.1'
						}),
				'actual_start': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'actual_finish': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'notes': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 2,
						'placeholder': 'Progress update notes...'
						}),
				}