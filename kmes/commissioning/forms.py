# from django import forms
# from django.utils import timezone
# from ..commissioning.models import (
# 	CommissioningSystem, TestProcedure, TestRecord,
# 	PunchItem, PunchItemPhoto
# 	)
# from ..core.models import System
#
#
# class CommissioningSystemForm(forms.ModelForm):
# 	"""Form for creating and updating commissioning systems."""
#
# 	class Meta:
# 		model = CommissioningSystem
# 		fields = [
# 				'system', 'status', 'planned_start', 'planned_finish',
# 				'actual_start', 'actual_finish', 'lead_engineer', 'notes'
# 				]
# 		widgets = {
# 				'system': forms.Select(attrs={'class': 'form-select'}),
# 				'status': forms.Select(attrs={'class': 'form-select'}),
# 				'planned_start': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'planned_finish': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'actual_start': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'actual_finish': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'lead_engineer': forms.Select(attrs={'class': 'form-select'}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Commissioning notes...'
# 						}),
# 				}
#
#
# class TestProcedureForm(forms.ModelForm):
# 	"""Form for creating and updating test procedures."""
#
# 	class Meta:
# 		model = TestProcedure
# 		fields = [
# 				'commissioning_system', 'code', 'description',
# 				'test_type', 'procedure_document', 'prerequisites',
# 				'equipment_tags', 'duration_hours', 'is_mandatory'
# 				]
# 		widgets = {
# 				'commissioning_system': forms.Select(attrs={'class': 'form-select'}),
# 				'code': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., TEST-HPGR-001'
# 						}),
# 				'description': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'e.g., HPGR Motor Solo Run Test - 4 hours'
# 						}),
# 				'test_type': forms.Select(attrs={'class': 'form-select'}),
# 				'procedure_document': forms.Select(attrs={'class': 'form-select'}),
# 				'prerequisites': forms.SelectMultiple(attrs={
# 						'class': 'form-select',
# 						'size': '5'
# 						}),
# 				'equipment_tags': forms.SelectMultiple(attrs={
# 						'class': 'form-select',
# 						'size': '5'
# 						}),
# 				'duration_hours': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'min': '0',
# 						'step': '0.5',
# 						'placeholder': 'Estimated duration in hours'
# 						}),
# 				'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
# 				}
#
# 	def __init__(self, *args, **kwargs):
# 		super().__init__(*args, **kwargs)
# 		if self.instance.pk:
# 			# Exclude self from prerequisites
# 			self.fields['prerequisites'].queryset = TestProcedure.objects.exclude(
# 					pk=self.instance.pk
# 					)
#
#
# class TestRecordForm(forms.ModelForm):
# 	"""Form for recording test execution results."""
#
# 	class Meta:
# 		model = TestRecord
# 		fields = [
# 				'test_procedure', 'test_number', 'executed_by',
# 				'witnessed_by', 'start_datetime', 'end_datetime',
# 				'result', 'comments'
# 				]
# 		widgets = {
# 				'test_procedure': forms.Select(attrs={'class': 'form-select'}),
# 				'test_number': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'min': '1'
# 						}),
# 				'executed_by': forms.Select(attrs={'class': 'form-select'}),
# 				'witnessed_by': forms.Select(attrs={'class': 'form-select'}),
# 				'start_datetime': forms.DateTimeInput(attrs={
# 						'class': 'form-control',
# 						'type': 'datetime-local'
# 						}),
# 				'end_datetime': forms.DateTimeInput(attrs={
# 						'class': 'form-control',
# 						'type': 'datetime-local'
# 						}),
# 				'result': forms.Select(attrs={'class': 'form-select'}),
# 				'comments': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Test results and observations...'
# 						}),
# 				}
#
#
# class PunchItemForm(forms.ModelForm):
# 	"""Form for creating new punch items."""
#
# 	class Meta:
# 		model = PunchItem
# 		fields = [
# 				'project', 'equipment_tag', 'system', 'test_record',
# 				'punch_number', 'description', 'category',
# 				'assigned_to_contractor', 'assigned_to', 'due_date'
# 				]
# 		widgets = {
# 				'project': forms.Select(attrs={'class': 'form-select'}),
# 				'equipment_tag': forms.Select(attrs={'class': 'form-select'}),
# 				'system': forms.Select(attrs={'class': 'form-select'}),
# 				'test_record': forms.Select(attrs={'class': 'form-select'}),
# 				'punch_number': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., PUNCH-2024-001'
# 						}),
# 				'description': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Detailed description of the defect or outstanding work...'
# 						}),
# 				'category': forms.Select(attrs={'class': 'form-select'}),
# 				'assigned_to_contractor': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., ABC Electrical Ltd.'
# 						}),
# 				'assigned_to': forms.Select(attrs={'class': 'form-select'}),
# 				'due_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				}
#
# 	def __init__(self, *args, **kwargs):
# 		project_id = kwargs.pop('project_id', None)
# 		super().__init__(*args, **kwargs)
#
# 		if project_id:
# 			from ..core.models import EquipmentTag
# 			self.fields['equipment_tag'].queryset = EquipmentTag.objects.filter(
# 					project_id=project_id
# 					)
# 			self.fields['system'].queryset = System.objects.filter(
# 					project_id=project_id
# 					)
# 			self.fields['test_record'].queryset = TestRecord.objects.filter(
# 					test_procedure__commissioning_system__system__project_id=project_id
# 					)
#
#
# class PunchItemResolveForm(forms.ModelForm):
# 	"""Form for resolving a punch item."""
#
# 	class Meta:
# 		model = PunchItem
# 		fields = ['status', 'resolved_date', 'notes']
# 		widgets = {
# 				'status': forms.Select(
# 						choices=[
# 								('RESL', 'Resolved'),
# 								('REJ', 'Rejected - Cannot be resolved'),
# 								],
# 						attrs={'class': 'form-select'}
# 						),
# 				'resolved_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Describe how the issue was resolved...'
# 						}),
# 				}
#
# 	def clean(self):
# 		cleaned_data = super().clean()
# 		status = cleaned_data.get('status')
# 		resolved_date = cleaned_data.get('resolved_date')
#
# 		if status == 'RESL' and not resolved_date:
# 			self.fields['resolved_date'].required = True
# 			raise forms.ValidationError(
# 					"Resolution date is required when marking as resolved."
# 					)
# 		return cleaned_data
#
#
# class PunchItemVerifyForm(forms.ModelForm):
# 	"""Form for verifying a resolved punch item."""
#
# 	class Meta:
# 		model = PunchItem
# 		fields = ['status', 'verified_date', 'notes']
# 		widgets = {
# 				'status': forms.Select(
# 						choices=[
# 								('CLSD', 'Verified Closed'),
# 								('IPRO', 'Return to In Progress - Not satisfied'),
# 								],
# 						attrs={'class': 'form-select'}
# 						),
# 				'verified_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Verification comments...'
# 						}),
# 				}
#
# 	def __init__(self, *args, **kwargs):
# 		super().__init__(*args, **kwargs)
# 		self.fields['verified_date'].initial = timezone.now().date()
#
#
# class PunchItemPhotoForm(forms.ModelForm):
# 	"""Form for uploading punch item photos."""
#
# 	class Meta:
# 		model = PunchItemPhoto
# 		fields = ['photo', 'photo_type', 'caption']
# 		widgets = {
# 				'photo': forms.FileInput(attrs={
# 						'class': 'form-control',
# 						'accept': 'image/*'
# 						}),
# 				'photo_type': forms.Select(attrs={'class': 'form-select'}),
# 				'caption': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Photo description'
# 						}),
# 				}
#