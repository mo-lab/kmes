# from django import forms
# from django.core.exceptions import ValidationError
# from django.utils import timezone
# from models import (
# 	Employee, Certification, Timesheet,
# 	ToolPlant, ToolAssignment
# 	)
# from ..construction.models import WorkPackage
#
#
# class EmployeeForm(forms.ModelForm):
# 	"""Form for creating and updating employees."""
#
# 	class Meta:
# 		model = Employee
# 		fields = [
# 				'employee_id', 'first_name', 'last_name',
# 				'company', 'trade', 'phone', 'email',
# 				'is_active', 'hire_date', 'notes'
# 				]
# 		widgets = {
# 				'employee_id': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., EMP-001'
# 						}),
# 				'first_name': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'First name'
# 						}),
# 				'last_name': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Last name'
# 						}),
# 				'company': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., ABC Construction Ltd.'
# 						}),
# 				'trade': forms.Select(attrs={'class': 'form-select'}),
# 				'phone': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': '+1 234 567 8900'
# 						}),
# 				'email': forms.EmailInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'employee@company.com'
# 						}),
# 				'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
# 				'hire_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Additional notes...'
# 						}),
# 				}
#
#
# class CertificationForm(forms.ModelForm):
# 	"""Form for managing employee certifications."""
#
# 	class Meta:
# 		model = Certification
# 		fields = [
# 				'employee', 'name', 'issuing_body',
# 				'certificate_number', 'issue_date',
# 				'expiry_date', 'is_valid', 'document_upload', 'notes'
# 				]
# 		widgets = {
# 				'employee': forms.Select(attrs={'class': 'form-select'}),
# 				'name': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., Electrical License'
# 						}),
# 				'issuing_body': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., State Electrical Board'
# 						}),
# 				'certificate_number': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Certificate/license number'
# 						}),
# 				'issue_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'expiry_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'is_valid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
# 				'document_upload': forms.FileInput(attrs={'class': 'form-control'}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 2,
# 						'placeholder': 'Additional notes...'
# 						}),
# 				}
#
# 	def clean(self):
# 		cleaned_data = super().clean()
# 		issue_date = cleaned_data.get('issue_date')
# 		expiry_date = cleaned_data.get('expiry_date')
#
# 		if issue_date and expiry_date and expiry_date < issue_date:
# 			raise ValidationError("Expiry date cannot be before issue date.")
# 		return cleaned_data
#
#
# class TimesheetForm(forms.ModelForm):
# 	"""Form for daily timesheet entries."""
#
# 	class Meta:
# 		model = Timesheet
# 		fields = [
# 				'employee', 'work_package', 'date',
# 				'hours_worked', 'overtime_hours', 'notes'
# 				]
# 		widgets = {
# 				'employee': forms.Select(attrs={'class': 'form-select'}),
# 				'work_package': forms.Select(attrs={'class': 'form-select'}),
# 				'date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'hours_worked': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'min': '0',
# 						'max': '24',
# 						'step': '0.5',
# 						'placeholder': 'Regular hours'
# 						}),
# 				'overtime_hours': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'min': '0',
# 						'max': '12',
# 						'step': '0.5',
# 						'placeholder': 'Overtime hours'
# 						}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 2,
# 						'placeholder': 'Work description or notes...'
# 						}),
# 				}
#
# 	def clean(self):
# 		cleaned_data = super().clean()
# 		hours_worked = cleaned_data.get('hours_worked', 0)
# 		overtime_hours = cleaned_data.get('overtime_hours', 0)
#
# 		if hours_worked + overtime_hours > 24:
# 			raise ValidationError("Total hours cannot exceed 24 hours in a day.")
# 		return cleaned_data
#
#
# class TimesheetBulkCreateForm(forms.Form):
# 	"""Form for bulk creating timesheets for multiple employees."""
#
# 	work_package = forms.ModelChoiceField(
# 			queryset=WorkPackage.objects.all(),
# 			widget=forms.Select(attrs={'class': 'form-select'})
# 			)
# 	date = forms.DateField(
# 			widget=forms.DateInput(attrs={
# 					'class': 'form-control',
# 					'type': 'date'
# 					})
# 			)
# 	employees = forms.ModelMultipleChoiceField(
# 			queryset=Employee.objects.filter(is_active=True),
# 			widget=forms.SelectMultiple(attrs={
# 					'class': 'form-select',
# 					'size': '10'
# 					})
# 			)
# 	default_hours = forms.DecimalField(
# 			max_digits=4, decimal_places=2, initial=8.00,
# 			widget=forms.NumberInput(attrs={
# 					'class': 'form-control',
# 					'min': '0',
# 					'max': '24',
# 					'step': '0.5'
# 					})
# 			)
# 	overtime_hours = forms.DecimalField(
# 			max_digits=4, decimal_places=2, initial=0.00,
# 			required=False,
# 			widget=forms.NumberInput(attrs={
# 					'class': 'form-control',
# 					'min': '0',
# 					'max': '12',
# 					'step': '0.5'
# 					})
# 			)
#
#
# class ToolPlantForm(forms.ModelForm):
# 	"""Form for managing tools and plant equipment."""
#
# 	class Meta:
# 		model = ToolPlant
# 		fields = [
# 				'asset_number', 'tool_type', 'make', 'model',
# 				'capacity', 'status', 'current_location',
# 				'last_maintenance_date', 'next_maintenance_due', 'notes'
# 				]
# 		widgets = {
# 				'asset_number': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., CRANE-001'
# 						}),
# 				'tool_type': forms.Select(attrs={'class': 'form-select'}),
# 				'make': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., Liebherr, Caterpillar'
# 						}),
# 				'model': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., LTM 1100-5.2'
# 						}),
# 				'capacity': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': "e.g., '100T', '500kVA'"
# 						}),
# 				'status': forms.Select(attrs={'class': 'form-select'}),
# 				'current_location': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., Area 100 - Near Crusher'
# 						}),
# 				'last_maintenance_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'next_maintenance_due': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Additional notes...'
# 						}),
# 				}
#
#
# class ToolPlantMaintenanceForm(forms.ModelForm):
# 	"""Form for updating maintenance status of tools."""
#
# 	class Meta:
# 		model = ToolPlant
# 		fields = [
# 				'status', 'last_maintenance_date',
# 				'next_maintenance_due', 'notes'
# 				]
# 		widgets = {
# 				'status': forms.Select(attrs={'class': 'form-select'}),
# 				'last_maintenance_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'next_maintenance_due': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Maintenance notes...'
# 						}),
# 				}
#
#
# class ToolAssignmentForm(forms.ModelForm):
# 	"""Form for assigning tools to work packages."""
#
# 	class Meta:
# 		model = ToolAssignment
# 		fields = [
# 				'tool_plant', 'work_package',
# 				'assignment_start', 'assignment_end', 'notes'
# 				]
# 		widgets = {
# 				'tool_plant': forms.Select(attrs={'class': 'form-select'}),
# 				'work_package': forms.Select(attrs={'class': 'form-select'}),
# 				'assignment_start': forms.DateTimeInput(attrs={
# 						'class': 'form-control',
# 						'type': 'datetime-local'
# 						}),
# 				'assignment_end': forms.DateTimeInput(attrs={
# 						'class': 'form-control',
# 						'type': 'datetime-local'
# 						}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 2,
# 						'placeholder': 'Assignment notes...'
# 						}),
# 				}
#
# 	def __init__(self, *args, **kwargs):
# 		super().__init__(*args, **kwargs)
# 		# Only show available tools
# 		self.fields['tool_plant'].queryset = ToolPlant.objects.filter(
# 				status__in=['AVL', 'INUS']
# 				)
#
# 	def clean(self):
# 		cleaned_data = super().clean()
# 		assignment_start = cleaned_data.get('assignment_start')
# 		assignment_end = cleaned_data.get('assignment_end')
#
# 		if assignment_start and assignment_end and assignment_end < assignment_start:
# 			raise ValidationError(
# 					"Assignment end cannot be before assignment start."
# 					)
# 		return cleaned_data