from django import forms
from django.utils import timezone

from .models import (
	WorkPackage, WorkPackageItem, DailyProgressReport,
	InstalledItemCheck, InstallationCheckPhoto, DailyProcessReportEmployees, WorkPackageRequirements
	)
from core.models import EquipmentTag,Project,Area,System


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
				'project':        forms.Select(attrs={'class': 'form-select'}),
				'code':           forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'e.g., WP-CRUSH-INST-001'
								}
						),
				'name':           forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'e.g., Install HPGR and Feed Chute'
								}
						),
				'area':           forms.Select(attrs={'class': 'form-select'}),
				'system':         forms.Select(attrs={'class': 'form-select'}),
				'description':    forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        4,
								'placeholder': 'Detailed scope of work...'
								}
						),
				'supervisor':     forms.Select(attrs={'class': 'form-select'}),
				'contractor':     forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'e.g., ABC Construction Ltd.'
								}
						),
				'planned_start':  forms.DateInput(
						attrs={
								'class': 'form-control',
								'type':  'date'
								}
						),
				'planned_finish': forms.DateInput(
						attrs={
								'class': 'form-control',
								'type':  'date'
								}
						),
				'status':         forms.Select(attrs={'class': 'form-select'}),
				'priority':       forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1=Highest, 5=Lowest'}),
				'notes':          forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        3,
								'placeholder': 'Additional notes...'
								}
						),
				}
		
	def __init__(self, *args, **kwargs):
		project_id = kwargs.pop('project_id', None)
	
		super().__init__(*args, **kwargs)
		
		if project_id:
			self.fields['project'].queryset = Project.objects.filter(pk=project_id)
			self.fields['area'].queryset = Area.objects.filter(project_id=project_id)
			self.fields['system'].queryset = System.objects.filter(project_id=project_id)
			
			
	def clean(self):
		cleaned_data = super().clean()
		planned_start = cleaned_data.get('planned_start')
		planned_finish = cleaned_data.get('planned_finish')
		
		if planned_start and planned_finish and planned_finish < planned_start:
			raise forms.ValidationError(
					"Planned finish date cannot be before planned start date."
					)
		return cleaned_data


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
				'work_package':               forms.Select(attrs={'class': 'form-select'}),
				'report_date':                forms.DateInput(
						attrs={
								'class': 'form-control',
								'type':  'date'
								}
						),
				'work_performed_description': forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        4,
								'placeholder': 'Describe work performed today...'
								}
						),
				'issues_encountered':         forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        3,
								'placeholder': 'Any issues, delays, or safety concerns...'
								}
						),
				'weather_conditions':         forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'e.g., Sunny, Cloudy, Rainy'
								}
						),
				'temperature_celsius':        forms.NumberInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'Temperature in °C'
								}
						),
				'manpower_count':             forms.NumberInput(
						attrs={
								'class': 'form-control',
								'min':   '0'
								}
						),
				'hours_worked':               forms.NumberInput(
						attrs={
								'class': 'form-control',
								'min':   '0',
								'step':  '0.5'
								}
						),
				}
		
		
class InstalledItemCheckForm(forms.ModelForm):
	class Meta:
		model = InstalledItemCheck
		fields = [
				'equipment_tag', 'checked_date',
				'foundation_ok', 'grouting_ok', 'bolting_ok',
				'alignment_ok', 'electrical_ok', 'status', 'comments'
				]
		widgets = {
				'equipment_tag': forms.Select(attrs={'class': 'form-select'}),
				'checked_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
				'foundation_ok': forms.NullBooleanSelect(attrs={'class': 'form-select'}),
				'grouting_ok': forms.NullBooleanSelect(attrs={'class': 'form-select'}),
				'bolting_ok': forms.NullBooleanSelect(attrs={'class': 'form-select'}),
				'alignment_ok': forms.NullBooleanSelect(attrs={'class': 'form-select'}),
				'electrical_ok': forms.NullBooleanSelect(attrs={'class': 'form-select'}),
				'status': forms.Select(attrs={'class': 'form-select'}),
				'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
				}
	
	def __init__(self, *args, **kwargs):
		tag_id = kwargs.pop('tag_id', None)
		super().__init__(*args, **kwargs)
		if tag_id:
			self.fields['equipment_tag'].initial = tag_id
			

# Inline formset for photos
PhotoFormSet = forms.inlineformset_factory(
		InstalledItemCheck,
		InstallationCheckPhoto,
		fields=('photo', 'caption'),
		extra=3,
		can_delete=True,
		widgets={
				'photo': forms.FileInput(attrs={'class': 'form-control'}),
				'caption': forms.TextInput(attrs={'class': 'form-control'}),
				}
		)


class WorkPackageProgressUpdateForm(forms.ModelForm):
	"""Simplified form for quick progress updates."""
	
	class Meta:
		model = WorkPackage
		fields = ['status', 'percent_complete', 'actual_start', 'actual_finish', 'notes']
		widgets = {
				'status':           forms.Select(attrs={'class': 'form-select'}),
				'percent_complete': forms.NumberInput(
						attrs={
								'class': 'form-control',
								'min':   '0',
								'max':   '100',
								'step':  '0.1'
								}
						),
				'actual_start':     forms.DateInput(
						attrs={
								'class': 'form-control',
								'type':  'date'
								}
						),
				'actual_finish':    forms.DateInput(
						attrs={
								'class': 'form-control',
								'type':  'date'
								}
						),
				'notes':            forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        2,
								'placeholder': 'Progress update notes...'
								}
						),
				}


class WorkPackageSearchForm(forms.Form):
	"""Form for searching and filtering work packages."""
	
	project = forms.CharField(
			required=False,
			widget=forms.Select(
					attrs={
							'class':    'form-select form-select-sm',
							'onchange': 'this.form.submit()'
							}
					)
			)
	
	area = forms.CharField(
			required=False,
			widget=forms.Select(
					attrs={
							'class':    'form-select form-select-sm',
							'onchange': 'this.form.submit()'
							}
					)
			)
	company = forms.CharField(
			required=False,
			widget=forms.Select(
					attrs={
							'class':    'form-select form-select-sm',
							'onchange': 'this.form.submit()'
							}
					)
			)
	status = forms.ChoiceField(
			choices=[('', 'All Statuses')] + list(WorkPackage.Status.choices),
			required=False,
			widget=forms.Select(
					attrs={
							'class':    'form-select form-select-sm',
							'onchange': 'this.form.submit()'
							}
					)
			)
	
	priority = forms.ChoiceField(
			choices=[('', 'All Priorities')] + [(i, f'{i} - {["", "Highest", "High", "Medium", "Low", "Lowest"][i]}') for i in range(1, 6)],
			required=False,
			widget=forms.Select(
					attrs={
							'class':    'form-select form-select-sm',
							'onchange': 'this.form.submit()'
							}
					)
			)
	
	contractor = forms.CharField(
			required=False,
			widget=forms.TextInput(
					attrs={
							'class':       'form-control form-control-sm',
							'placeholder': 'Filter by contractor...'
							}
					)
			)
	
	search = forms.CharField(
			required=False,
			widget=forms.TextInput(
					attrs={
							'class':       'form-control form-control-sm',
							'placeholder': 'Search code, name, description...'
							}
					)
			)
	
	date_from = forms.DateField(
			required=False,
			widget=forms.DateInput(
					attrs={
							'class':    'form-control form-control-sm',
							'type':     'date',
							'onchange': 'this.form.submit()'
							}
					)
			)
	
	date_to = forms.DateField(
			required=False,
			widget=forms.DateInput(
					attrs={
							'class':    'form-control form-control-sm',
							'type':     'date',
							'onchange': 'this.form.submit()'
							}
					)
			)
	
	overdue_only = forms.BooleanField(
			required=False,
			widget=forms.CheckboxInput(
					attrs={
							'class':    'form-check-input',
							'onchange': 'this.form.submit()'
							}
					)
			)


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
				'work_package':               forms.Select(
						attrs={
								'class':    'form-select',
								'required': 'required'
								}
						),
				'report_date':                forms.DateInput(
						attrs={
								'class':    'form-control',
								'type':     'date',
								'required': 'required'
								}
						),
				'work_performed_description': forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        6,
								'placeholder': 'Describe the work performed today in detail...\n\nInclude:\n- Equipment tags worked on\n- Tasks completed\n- Materials used\n- Measurements taken\n- Any deviations from plan',
								'required':    'required'
								}
						),
				'issues_encountered':         forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        3,
								'placeholder': 'Describe any issues, delays, safety concerns, or obstacles encountered...'
								}
						),
				'weather_conditions':         forms.TextInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'e.g., Sunny, Cloudy, Rainy',
								'readonly':    'readonly',
								'style':       'display: none;'
								}
						),
				'temperature_celsius':        forms.NumberInput(
						attrs={
								'class':       'form-control',
								'placeholder': 'Temp in °C',
								'min':         '-50',
								'max':         '60'
								}
						),
				'manpower_count':             forms.NumberInput(
						attrs={
								'class':    'form-control',
								'min':      '0',
								'required': 'required',
								'style':    'width: 80px; display: inline;'
								}
						),
				'hours_worked':               forms.NumberInput(
						attrs={
								'class':       'form-control',
								'min':         '0',
								'step':        '0.5',
								'placeholder': 'Total man-hours'
								}
						),
				}
	
	def __init__(self, *args, **kwargs):
		work_package_id = kwargs.pop('work_package_id', None)
		super().__init__(*args, **kwargs)
		
		if work_package_id:
			self.fields['work_package'].queryset = WorkPackage.objects.filter(
					pk=work_package_id
					)
			self.fields['work_package'].initial = work_package_id
			self.fields['work_package'].widget = forms.HiddenInput()
		else:
			self.fields['work_package'].queryset = WorkPackage.objects.filter(
					status__in=['IPRO', 'MOB', 'NSTA']
					).select_related('project', 'area')
	
	def clean(self):
		cleaned_data = super().clean()
		report_date = cleaned_data.get('report_date')
		
		if report_date and report_date > timezone.now().date():
			self.add_error('report_date', 'Report date cannot be in the future.')
		
		return cleaned_data


class WorkPackageItemForm(forms.ModelForm):
	"""Form for adding a single equipment tag to a work package."""
	
	class Meta:
		model = WorkPackageItem
		fields = ['equipment_tag', 'sequence_number', 'notes']
		widgets = {
				'equipment_tag':   forms.Select(
						attrs={
								'class':    'form-select',
								'required': 'required'
								}
						),
				'sequence_number': forms.NumberInput(
						attrs={
								'class': 'form-control',
								'min':   '1'
								}
						),
				'notes':           forms.Textarea(
						attrs={
								'class':       'form-control',
								'rows':        2,
								'placeholder': 'Optional notes for this item...'
								}
						),
				}
	
	def __init__(self, *args, **kwargs):
		work_package_id = kwargs.pop('work_package_id', None)
		super().__init__(*args, **kwargs)
		
		if work_package_id:
			work_package = WorkPackage.objects.get(pk=work_package_id)
			# Only show tags from the same project that aren't already in this WP
			# existing_ids = WorkPackageItem.objects.filter(
			# 		work_package_id=work_package_id
			# 		).values_list('equipment_tag_id', flat=True)
			
			self.fields['equipment_tag'].queryset = EquipmentTag.objects.filter(
					project=work_package.project
					).select_related('area').order_by('tag_number') #.exclude(pk__in=existing_ids).


class WorkPackageItemBulkForm(forms.Form):
	"""Form for bulk adding equipment tags to a work package."""
	
	BULK_MODES = [
			('selected', 'Selected Tags'),
			('area', 'All Tags in Area'),
			('system', 'All Tags in System'),
			('type', 'All Tags of Type'),
			('status', 'All Tags with Status'),
			('search', 'Search Results'),
			]
	
	bulk_mode = forms.ChoiceField(
			choices=BULK_MODES,
			initial='selected',
			widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
			)
	
	# For selected mode
	equipment_tags = forms.CharField(
			required=False,
			widget=forms.HiddenInput(),
			help_text="Comma-separated tag IDs"
			)
	
	# For area mode
	area = forms.IntegerField(
			required=False,
			widget=forms.HiddenInput()
			)
	
	# For system mode
	system = forms.IntegerField(
			required=False,
			widget=forms.HiddenInput()
			)
	
	# For type mode
	equipment_type = forms.ChoiceField(
			choices=[('', 'Select Type')] + list(EquipmentTag.EquipmentType.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	
	# For status mode
	tag_status = forms.ChoiceField(
			choices=[('', 'Select Status')] + list(EquipmentTag.Status.choices),
			required=False,
			widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
			)
	
	# For search mode
	search_term = forms.CharField(
			required=False,
			widget=forms.TextInput(
					attrs={
							'class':       'form-control form-control-sm',
							'placeholder': 'Search tag number or description...'
							}
					)
			)
	
	def __init__(self, *args, **kwargs):
		work_package_id = kwargs.pop('work_package_id', None)
		super().__init__(*args, **kwargs)
		self.work_package_id = work_package_id


class DailyReportSearchForm(forms.Form):
	"""Form for searching and filtering daily progress reports."""
	
	project = forms.CharField(
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	work_package = forms.CharField(
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	area = forms.CharField(
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	company = forms.CharField(
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	reported_by = forms.CharField(
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	has_issues = forms.BooleanField(
			required=False,
			widget=forms.CheckboxInput(attrs={
					'class': 'form-check-input',
					'onchange': 'this.form.submit()'
					})
			)
	
	is_approved = forms.ChoiceField(
			choices=[('', 'All'), ('true', 'Approved'), ('false', 'Pending')],
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	weather = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control form-control-sm',
					'placeholder': 'e.g., Sunny, Rainy...'
					})
			)
	
	date_from = forms.DateField(
			required=False,
			widget=forms.DateInput(attrs={
					'class': 'form-control form-control-sm',
					'type': 'date',
					'onchange': 'this.form.submit()'
					})
			)
	
	date_to = forms.DateField(
			required=False,
			widget=forms.DateInput(attrs={
					'class': 'form-control form-control-sm',
					'type': 'date',
					'onchange': 'this.form.submit()'
					})
			)
	
	search = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control form-control-sm',
					'placeholder': 'Search reports...'
					})
			)

class DailyProccessReportEmployeeForm(forms.ModelForm):
	class Meta:
		model = DailyProcessReportEmployees
		fields = ['employee', 'daily_report', 'is_working', 'timesheet']
		
		# Optional: Add widgets for styling (e.g., Bootstrap classes)
		widgets = {
				'employee': forms.Select(attrs={'class': 'form-control'}),
				'daily_report': forms.Select(attrs={'class': 'form-control'}),
				'is_working': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
				'timesheet': forms.Select(attrs={'class': 'form-control'}),
				}


class DailyProgressReportForm2(forms.ModelForm):
	"""Form for daily progress reports – employee selection handled in template."""
	
	class Meta:
		model = DailyProgressReport
		fields = [
				'work_package', 'report_date',
				'work_performed_description', 'issues_encountered',
				'weather_conditions', 'temperature_celsius',
				'manpower_count', 'hours_worked'
				]
		widgets = {
				'work_package': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'report_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date',
						'required': 'required'
						}),
				'work_performed_description': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 4,
						'placeholder': 'Describe the work performed today in detail...',
						'required': 'required'
						}),
				'issues_encountered': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 2,
						'placeholder': 'Any issues, delays, safety concerns...'
						}),
				'weather_conditions': forms.TextInput(attrs={
						'class': 'form-control',
						'readonly': 'readonly',
						'style': 'display:none;'  # hidden, we use buttons
						}),
				'temperature_celsius': forms.NumberInput(attrs={
						'class': 'form-control',
						'placeholder': '°C',
						'min': -50, 'max': 60
						}),
				'manpower_count': forms.NumberInput(attrs={
						'class': 'form-control',
						'min': 0,
						'readonly': 'readonly',  # will be auto-calculated from selected employees
						}),
				'hours_worked': forms.NumberInput(attrs={
						'class': 'form-control',
						'min': 0,
						'step': 0.5,
						'placeholder': 'Total man-hours'
						}),
				}
	
	def __init__(self, *args, **kwargs):
		work_package_id = kwargs.pop('work_package_id', None)
		super().__init__(*args, **kwargs)
		
		# Filter work packages to those active
		self.fields['work_package'].queryset = WorkPackage.objects.filter(
				status__in=['IPRO', 'MOB', 'NSTA']
				).select_related('project', 'area')
		
		if work_package_id:
			self.fields['work_package'].initial = work_package_id
			self.fields['work_package'].widget = forms.HiddenInput()
	
	def clean(self):
		cleaned_data = super().clean()
		date = cleaned_data.get('report_date')
		if date and date > timezone.now().date():
			self.add_error('report_date', 'Report date cannot be in the future.')
		return cleaned_data

class WorkPackageRequirementsForm(forms.ModelForm):
	class Meta:
		model = WorkPackageRequirements
		fields = ['name', 'description', 'priority']
		widgets = {
				'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان نیازمندی'}),
				'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'توضیح کوتاه'}),
				'priority': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
				}