# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomLoginForm(AuthenticationForm):
	"""Custom login form with Persian labels and styling."""
	
	username = forms.CharField(
			widget=forms.TextInput(
					attrs={
							'class':       'form-control',
							'placeholder': 'نام کاربری یا ایمیل',
							'autofocus':   True,
							}
					),
			label='نام کاربری'
			)
	password = forms.CharField(
			widget=forms.PasswordInput(
					attrs={
							'class':       'form-control',
							'placeholder': 'رمز عبور',
							}
					),
			label='رمز عبور'
			)
	remember_me = forms.BooleanField(
			required=False,
			initial=True,
			widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
			label='مرا به خاطر بسپار'
			)
