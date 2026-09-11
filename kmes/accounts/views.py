from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View
from .forms import CustomLoginForm


class CustomLoginView(LoginView):
	"""Custom login view."""
	form_class = CustomLoginForm
	template_name = 'rtl/accounts/login.html'
	redirect_authenticated_user = True
	
	def get_success_url(self):
		return reverse_lazy('dashboard')
	
	def form_valid(self, form):
		"""Security check and session handling."""
		remember_me = form.cleaned_data.get('remember_me')
		if not remember_me:
			# Session expires when browser closes
			self.request.session.set_expiry(0)
		else:
			# Session lasts 30 days
			self.request.session.set_expiry(30 * 24 * 60 * 60)
		
		messages.success(self.request, f'خوش آمدید، {form.get_user().get_full_name() or form.get_user().username}!')
		return super().form_valid(form)
	
	def form_invalid(self, form):
		messages.error(self.request, 'نام کاربری یا رمز عبور اشتباه است.')
		return super().form_invalid(form)


class CustomLogoutView(LogoutView):
	"""Custom logout view."""
	next_page = reverse_lazy('accounts:login')
	
	def dispatch(self, request, *args, **kwargs):
		if request.user.is_authenticated:
			messages.info(request, f'خداحافظ، {request.user.get_full_name() or request.user.username}!')
		return super().dispatch(request, *args, **kwargs)
