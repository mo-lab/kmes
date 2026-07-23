from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Employee, Timesheet
from construction.models import WorkPackage

User = get_user_model()


class EmployeeForm(forms.ModelForm):
	"""Form for creating and updating employees."""
	
	class Meta:
		model = Employee
		fields = [
				'employee_id', 'user', 'first_name', 'last_name',
				'company', 'trade', 'phone', 'email',
				'is_active', 'hire_date', 'termination_date', 'notes'
				]
		widgets = {
				'employee_id': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'Auto-generated if left blank'
						}),
				'user': forms.Select(attrs={
						'class': 'form-select'
						}),
				'first_name': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'First name',
						'required': 'required'
						}),
				'last_name': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'Last name',
						'required': 'required'
						}),
				'company': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': 'Company or contractor name',
						'required': 'required'
						}),
				'trade': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'phone': forms.TextInput(attrs={
						'class': 'form-control',
						'placeholder': '+1 234 567 8900'
						}),
				'email': forms.EmailInput(attrs={
						'class': 'form-control',
						'placeholder': 'employee@company.com'
						}),
				'is_active': forms.CheckboxInput(attrs={
						'class': 'form-check-input'
						}),
				'hire_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'termination_date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date'
						}),
				'notes': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 3,
						'placeholder': 'Additional notes about this employee...'
						}),
				}
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		# Make some fields not required
		self.fields['employee_id'].required = False
		self.fields['termination_date'].required = False
		self.fields['phone'].required = False
		self.fields['email'].required = False
		self.fields['user'].required = False
		
		# Filter user queryset to only active users not already linked
		linked_user_ids = Employee.objects.exclude(
				pk=self.instance.pk if self.instance.pk else None
				).filter(user__isnull=False).values_list('user_id', flat=True)
		
		self.fields['user'].queryset = User.objects.filter(
				is_active=True
				).exclude(pk__in=linked_user_ids).order_by('username')
	
	def clean(self):
		cleaned_data = super().clean()
		hire_date = cleaned_data.get('hire_date')
		termination_date = cleaned_data.get('termination_date')
		
		if hire_date and termination_date and termination_date < hire_date:
			self.add_error('termination_date', 'Termination date cannot be before hire date.')
		
		return cleaned_data
	
	def clean_employee_id(self):
		employee_id = self.cleaned_data.get('employee_id')
		if employee_id:
			# Check uniqueness
			qs = Employee.objects.filter(employee_id=employee_id)
			if self.instance.pk:
				qs = qs.exclude(pk=self.instance.pk)
			if qs.exists():
				raise forms.ValidationError('This Employee ID is already in use.')
		return employee_id


class EmployeeSearchForm(forms.Form):
	"""Form for searching employees."""
	
	search = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control form-control-sm',
					'placeholder': 'Search by name, ID, company, email...'
					})
			)
	
	trade = forms.ChoiceField(
			choices=[('', 'All Trades')] + list(Employee.Trade.choices),
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	company = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control form-control-sm',
					'placeholder': 'Filter by company...'
					})
			)
	
	is_active = forms.ChoiceField(
			choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)

class TimesheetSearchForm(forms.Form):
	"""Form for searching and filtering timesheets."""
	
	employee = forms.CharField(
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
	
	project = forms.CharField(
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
					'onchange': 'this.form.submit()'
					})
			)
	
	company = forms.CharField(
			required=False,
			widget=forms.TextInput(attrs={
					'class': 'form-control form-control-sm',
					'placeholder': 'Filter by company...'
					})
			)
	
	trade = forms.ChoiceField(
			choices=[('', 'All Trades')] + list(Employee.Trade.choices),
			required=False,
			widget=forms.Select(attrs={
					'class': 'form-select form-select-sm',
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
					'placeholder': 'Search employee, WP code...'
					})
			)

class TimesheetForm(forms.ModelForm):
	"""Form for creating and updating timesheet entries."""
	
	class Meta:
		model = Timesheet
		fields = ['employee', 'work_package', 'date', 'hours_worked', 'overtime_hours', 'notes']
		widgets = {
				'employee': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'work_package': forms.Select(attrs={
						'class': 'form-select',
						'required': 'required'
						}),
				'date': forms.DateInput(attrs={
						'class': 'form-control',
						'type': 'date',
						'required': 'required'
						}),
				'hours_worked': forms.NumberInput(attrs={
						'class': 'form-control',
						'min': '0',
						'max': '24',
						'step': '0.5',
						'required': 'required',
						'style': 'width: 80px; text-align: center; font-size: 1.2rem; font-weight: bold;'
						}),
				'overtime_hours': forms.NumberInput(attrs={
						'class': 'form-control',
						'min': '0',
						'max': '12',
						'step': '0.5',
						'style': 'width: 80px; text-align: center; font-size: 1.2rem; font-weight: bold;'
						}),
				'notes': forms.Textarea(attrs={
						'class': 'form-control',
						'rows': 2,
						'placeholder': 'Optional notes about work performed...'
						}),
				}
	
	def __init__(self, *args, **kwargs):
		employee_id = kwargs.pop('employee_id', None)
		super().__init__(*args, **kwargs)
		
		# Filter active employees
		self.fields['employee'].queryset = Employee.objects.filter(
				is_active=True
				).order_by('company', 'last_name', 'first_name')
		
		# Filter active work packages
		self.fields['work_package'].queryset = WorkPackage.objects.filter(
				status__in=['IPRO', 'MOB', 'NSTA']
				).select_related('project').order_by('code')
		
		if employee_id:
			self.fields['employee'].initial = employee_id
			self.fields['employee'].widget = forms.HiddenInput()
	
	def clean(self):
		cleaned_data = super().clean()
		hours_worked = cleaned_data.get('hours_worked', 0)
		overtime_hours = cleaned_data.get('overtime_hours', 0)
		
		total_hours = hours_worked + overtime_hours
		
		if total_hours > 24:
			raise forms.ValidationError(
					f'Total hours ({total_hours}) cannot exceed 24 hours in a day.'
					)
		
		if total_hours <= 0:
			raise forms.ValidationError('Please enter at least some hours worked.')
		
		return cleaned_data


class TimesheetBulkForm(forms.Form):
	"""Form for bulk creating timesheet entries."""
	
	work_package = forms.ModelChoiceField(
			queryset=WorkPackage.objects.filter(status__in=['IPRO', 'MOB', 'NSTA']),
			widget=forms.Select(attrs={
					'class': 'form-select',
					'required': 'required'
					})
			)
	
	date = forms.DateField(
			widget=forms.DateInput(attrs={
					'class': 'form-control',
					'type': 'date',
					'required': 'required'
					}),
			initial=timezone.now().date()
			)
	
	employees = forms.ModelMultipleChoiceField(
			queryset=Employee.objects.filter(is_active=True).order_by('company', 'last_name'),
			widget=forms.SelectMultiple(attrs={
					'class': 'form-select',
					'size': '15',
					'required': 'required'
					})
			)
	
	default_hours = forms.DecimalField(
			max_digits=4,
			decimal_places=1,
			initial=8.0,
			widget=forms.NumberInput(attrs={
					'class': 'form-control',
					'min': '0',
					'max': '24',
					'step': '0.5'
					})
			)
	
	overtime_hours = forms.DecimalField(
			max_digits=4,
			decimal_places=1,
			initial=0.0,
			required=False,
			widget=forms.NumberInput(attrs={
					'class': 'form-control',
					'min': '0',
					'max': '12',
					'step': '0.5'
					})
			)
	
	notes = forms.CharField(
			required=False,
			widget=forms.Textarea(attrs={
					'class': 'form-control',
					'rows': 2,
					'placeholder': 'Optional notes for all entries...'
					})
			)