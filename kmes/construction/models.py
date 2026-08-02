from django.contrib import messages
from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from resources.models import Employee, Timesheet

User = get_user_model()


class WorkPackage(models.Model):
	"""A manageable chunk of installation work."""
	
	class Status(models.TextChoices):
		NOT_STARTED = 'NSTA', 'Not Started'
		MOBILIZING = 'MOB', 'Mobilizing'
		IN_PROGRESS = 'IPRO', 'In Progress'
		COMPLETE = 'COMP', 'Complete'
		ON_HOLD = 'HOLD', 'On Hold'
	
	project = models.ForeignKey(
			'core.Project', on_delete=models.CASCADE, related_name='work_packages'
			)
	code = models.CharField(max_length=50)
	name = models.CharField(max_length=500)
	area = models.ForeignKey(
			'core.Area', on_delete=models.PROTECT, related_name='work_packages'
			)
	system = models.ForeignKey(
			'core.System', on_delete=models.SET_NULL, null=True, blank=True,
			related_name='work_packages'
			)
	
	description = models.TextField(blank=True)
	supervisor = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='supervised_work_packages'
			)
	contractor = models.CharField(
			max_length=255, blank=True, help_text="Company executing the work"
			)
	
	planned_start = models.DateField()
	planned_finish = models.DateField()
	actual_start = models.DateField(null=True, blank=True)
	actual_finish = models.DateField(null=True, blank=True)
	
	status = models.CharField(max_length=4, choices=Status.choices, default=Status.NOT_STARTED)
	percent_complete = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
	
	priority = models.PositiveSmallIntegerField(default=3, help_text="1=Highest, 5=Lowest")
	notes = models.TextField(blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['code']
		verbose_name = 'Work Package'
		verbose_name_plural = 'Work Packages'
	
	def __str__(self):
		return f"{self.code} - {self.name[:80]}"
	
	@property
	def is_overdue(self):
		if self.actual_finish:
			return self.planned_finish < self.actual_finish
		return timezone.now().date() > self.planned_finish


class WorkPackageItem(models.Model):
	"""Links equipment tags to the work package that installs them."""
	
	work_package = models.ForeignKey(
			WorkPackage, on_delete=models.CASCADE, related_name='items'
			)
	equipment_tag = models.ForeignKey(
			'core.EquipmentTag', on_delete=models.CASCADE, related_name='work_package_items'
			)
	
	sequence_number = models.PositiveIntegerField(
			default=1, help_text="Order of installation"
			)
	installation_date = models.DateField(null=True, blank=True)
	is_complete = models.BooleanField(default=False)
	
	notes = models.TextField(blank=True)
	
	class Meta:
		unique_together = ['work_package', 'equipment_tag']
		ordering = ['sequence_number']
		verbose_name = 'Work Package Item'
		verbose_name_plural = 'Work Package Items'
	
	def __str__(self):
		return f"{self.work_package.code} -> {self.equipment_tag.tag_number}"


class DailyProgressReport(models.Model):
	"""Daily report for a work package."""
	
	work_package = models.ForeignKey(
			WorkPackage, on_delete=models.CASCADE, related_name='daily_reports'
			)
	report_date = models.DateField()
	reported_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, related_name='daily_reports'
			)
	
	work_performed_description = models.TextField()
	issues_encountered = models.TextField(blank=True)
	weather_conditions = models.CharField(max_length=200, blank=True)
	temperature_celsius = models.IntegerField(null=True, blank=True)
	
	manpower_count = models.PositiveIntegerField(default=0)
	hours_worked = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	
	is_approved = models.BooleanField(default=False)
	approved_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='approved_reports'
			)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		unique_together = ['work_package', 'report_date']
		ordering = ['-report_date']
		verbose_name = 'Daily Progress Report'
		verbose_name_plural = 'Daily Progress Reports'
	
	def __str__(self):
		return f"Report {self.work_package.code} - {self.report_date}"


class InstalledItemCheck(models.Model):
	"""Installation checklist for a single equipment tag."""
	
	class CheckStatus(models.TextChoices):
		PASS = 'PASS', 'Pass'
		FAIL_WITH_PUNCH = 'FAIL', 'Fail with Punch List'
		NOT_APPLICABLE = 'NA', 'Not Applicable'
	
	equipment_tag = models.ForeignKey(
			'core.EquipmentTag', on_delete=models.CASCADE, related_name='installation_checks'
			)
	checked_date = models.DateField()
	checked_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, related_name='installation_checks'
			)
	
	foundation_ok = models.BooleanField(null=True)
	grouting_ok = models.BooleanField(null=True)
	bolting_ok = models.BooleanField(null=True)
	alignment_ok = models.BooleanField(null=True)
	electrical_ok = models.BooleanField(null=True)
	
	status = models.CharField(max_length=4, choices=CheckStatus.choices, default=CheckStatus.PASS)
	comments = models.TextField(blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-checked_date']
		verbose_name = 'Installed Item Check'
		verbose_name_plural = 'Installed Item Checks'
	
	def __str__(self):
		return f"Install Check: {self.equipment_tag.tag_number} - {self.checked_date}"


class InstallationCheckPhoto(models.Model):
	"""Photos attached to an installation check."""
	
	installation_check = models.ForeignKey(
			InstalledItemCheck, on_delete=models.CASCADE, related_name='photos'
			)
	photo = models.ImageField(upload_to='installation_photos/%Y/%m/%d/')
	caption = models.CharField(max_length=255, blank=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		verbose_name = 'Installation Check Photo'
		verbose_name_plural = 'Installation Check Photos'


class DailyProcessReportEmployees(models.Model):
	employee = models.ForeignKey(
			'resources.Employee',  # adjust app label if needed
			on_delete=models.CASCADE,
			related_name='daily_employees'
			)
	daily_report = models.ForeignKey(
			'construction.DailyProgressReport',
			on_delete=models.CASCADE,
			related_name='employees'
			)
	is_working = models.BooleanField(default=False)
	timesheet = models.ForeignKey(
			'resources.Timesheet',
			on_delete=models.SET_NULL,  # Changed to SET_NULL to avoid cascading issues
			related_name='daily_reports',
			null=True,
			blank=True
			)
	
	class Meta:
		unique_together = ['employee', 'daily_report']
		ordering = ['employee', 'daily_report']
		verbose_name = 'Daily Process Report Employee'
		verbose_name_plural = 'Daily Process Report Employees'
	
	def __str__(self):
		return f"{self.employee} - {self.daily_report}"
	
	def save(self, *args, **kwargs):
		# Track the previous state to detect changes
		if self.pk:
			try:
				old_instance = DailyProcessReportEmployees.objects.get(pk=self.pk)
				was_working = old_instance.is_working
			except DailyProcessReportEmployees.DoesNotExist:
				was_working = False
		else:
			was_working = False
		
		# Prevent recursive saves
		if not hasattr(self, '_processing'):
			self._processing = False
		
		# --- Handle Timesheet Creation ---
		if self.is_working and not self.timesheet_id and not self._processing:
			self._processing = True
			try:
				# Gather needed data from the daily report
				work_package = getattr(self.daily_report, 'work_package', None)
				report_date = self.daily_report.report_date
				
				timesheet = Timesheet.objects.create(
						employee=self.employee,
						work_package=work_package,
						date=report_date,
						hours_worked=8,
						overtime_hours=0,
						notes=f"Auto-generated from daily report #{self.daily_report.pk}"
						)
				self.timesheet = timesheet
			finally:
				self._processing = False
		
		# --- Handle Timesheet Deletion ---
		elif not self.is_working and was_working and self.timesheet_id and not self._processing:
			self._processing = True
			try:
				timesheet_to_delete = self.timesheet
				self.timesheet = None  # Clear the reference first
				super().save(update_fields=['timesheet'])  # Save immediately to avoid FK issues
				
				# Now delete the timesheet
				if timesheet_to_delete:
					timesheet_to_delete.delete()
			finally:
				self._processing = False
		
		# --- Handle Timesheet Update (when hours may have changed) ---
		elif self.is_working and self.timesheet_id and not self._processing:
			self._processing = True
			try:
				timesheet = self.timesheet
				if timesheet:
					# Update timesheet details if needed
					work_package = getattr(self.daily_report, 'work_package', None)
					report_date = self.daily_report.report_date
					
					needs_update = False
					if timesheet.work_package != work_package:
						timesheet.work_package = work_package
						needs_update = True
					if timesheet.date != report_date:
						timesheet.date = report_date
						needs_update = True
					
					if needs_update:
						timesheet.save()
			finally:
				self._processing = False
		
		super().save(*args, **kwargs)


