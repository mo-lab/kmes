from django import forms
from django.contrib.auth import get_user_model
from .models import Employee

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