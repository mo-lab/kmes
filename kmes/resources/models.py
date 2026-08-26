from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Employee(models.Model):
	"""Personnel working on the project (staff and contractors)."""
	
	class Trade(models.TextChoices):
		MILLWRIGHT = 'MLWR', 'Millwright'
		ELECTRICIAN = 'ELEC', 'Electrician'
		WELDER = 'WELD', 'Welder'
		PIPE_FITTER = 'PIPE', 'Pipe Fitter'
		INSTRUMENT_TECH = 'INST', 'Instrument Technician'
		RIGGER = 'RIGG', 'Rigger'
		SUPERVISOR = 'SUPV', 'Supervisor'
		ENGINEER = 'ENGR', 'Engineer'
		SAFETY_OFFICER = 'SAFE', 'Safety Officer'
		LABORER = 'LAB', 'Laborer'
		OPERATOR = 'OPER', 'Operator'
		OTHER = 'OTHR', 'Other'
	
	user = models.OneToOneField(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='employee_profile'
			)
	employee_id = models.CharField(max_length=50, unique=True)
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	company = models.CharField(max_length=255, help_text="Contractor or employer name")
	trade = models.CharField(max_length=5, choices=Trade.choices)
	contractor=models.ForeignKey('Company', on_delete=models.SET_NULL, null=True)
	
	phone = models.CharField(max_length=50, blank=True)
	email = models.EmailField(blank=True)
	
	is_active = models.BooleanField(default=True)
	hire_date = models.DateField(null=True, blank=True)
	termination_date = models.DateField(null=True, blank=True)
	
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['last_name', 'first_name']
		verbose_name = 'Employee'
		verbose_name_plural = 'Employees'
	
	def __str__(self):
		return f"{self.first_name} {self.last_name} ({self.company})"
	
	@property
	def full_name(self):
		return f"{self.first_name} {self.last_name}"


class Certification(models.Model):
	"""Employee certifications with expiry tracking."""
	
	employee = models.ForeignKey(
			Employee, on_delete=models.CASCADE, related_name='certifications'
			)
	name = models.CharField(max_length=255)
	issuing_body = models.CharField(max_length=255, blank=True)
	certificate_number = models.CharField(max_length=100, blank=True)
	
	issue_date = models.DateField()
	expiry_date = models.DateField()
	
	is_valid = models.BooleanField(default=True)
	document_upload = models.FileField(
			upload_to='certifications/%Y/%m/%d/', null=True, blank=True
			)
	
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-expiry_date']
		verbose_name = 'Certification'
		verbose_name_plural = 'Certifications'
	
	def __str__(self):
		return f"{self.name} - {self.employee.full_name}"
	
	@property
	def is_expired(self):
		return timezone.now().date() > self.expiry_date


class Timesheet(models.Model):
	"""Daily time entries for employees against work packages."""
	
	employee = models.ForeignKey(
			Employee, on_delete=models.CASCADE, related_name='timesheets'
			)
	work_package = models.ForeignKey(
			'construction.WorkPackage', on_delete=models.CASCADE, related_name='timesheets',null=True,blank=True
			)
	
	date = models.DateField(default=timezone.now)
	hours_worked = models.DecimalField(max_digits=4, decimal_places=2,default=8)
	overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
	
	is_approved = models.BooleanField(default=False)
	approved_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='approved_timesheets'
			)
	
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		unique_together = ['employee', 'work_package', 'date']
		ordering = ['-date']
		verbose_name = 'Timesheet'
		verbose_name_plural = 'Timesheets'
	
	def __str__(self):
		return f"{self.employee.full_name} - {self.date} - {self.hours_worked}h"


class Company(models.Model):
	title = models.CharField(max_length=100, null=True, blank=True)
	
	def __str__(self):
		return self.title
	
	class Meta:
		ordering = ['title']
		verbose_name = 'Company'
		verbose_name_plural = 'Companies'
	
class ToolPlant(models.Model):
	"""Tools, equipment, and plant machinery available on site."""
	
	class ToolType(models.TextChoices):
		MOBILE_CRANE = 'CRANE', 'Mobile Crane'
		TOWER_CRANE = 'TWRN', 'Tower Crane'
		FORKLIFT = 'FORK', 'Forklift'
		WELDING_MACHINE = 'WELD', 'Welding Machine'
		GENERATOR = 'GEN', 'Generator'
		COMPRESSOR = 'COMP', 'Compressor'
		PUMP = 'PUMP', 'Pump'
		LIGHTING_PLANT = 'LITE', 'Lighting Plant'
		OTHER = 'OTHR', 'Other'
	
	class Status(models.TextChoices):
		AVAILABLE = 'AVL', 'Available'
		IN_USE = 'INUS', 'In Use'
		DOWN_FOR_MAINTENANCE = 'DOWN', 'Down for Maintenance'
		NEEDS_REPAIR = 'REPR', 'Needs Repair'
		RETIRED = 'RETD', 'Retired'
	
	asset_number = models.CharField(max_length=100, unique=True)
	tool_type = models.CharField(max_length=5, choices=ToolType.choices)
	make = models.CharField(max_length=100, blank=True)
	model = models.CharField(max_length=100, blank=True)
	capacity = models.CharField(
			max_length=100, blank=True, help_text="e.g., '100T', '500kVA'"
			)
	
	status = models.CharField(max_length=4, choices=Status.choices, default=Status.AVAILABLE)
	current_location = models.CharField(max_length=255, blank=True)
	
	last_maintenance_date = models.DateField(null=True, blank=True)
	next_maintenance_due = models.DateField(null=True, blank=True)
	
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['tool_type', 'asset_number']
		verbose_name = 'Tool/Plant'
		verbose_name_plural = 'Tools/Plant'
	
	def __str__(self):
		return f"{self.asset_number} - {self.get_tool_type_display()}"


class ToolAssignment(models.Model):
	"""Assignment of a tool/plant to a work package."""
	
	tool_plant = models.ForeignKey(
			ToolPlant, on_delete=models.CASCADE, related_name='assignments'
			)
	work_package = models.ForeignKey(
			'construction.WorkPackage', on_delete=models.CASCADE,
			related_name='tool_assignments'
			)
	
	assignment_start = models.DateTimeField()
	assignment_end = models.DateTimeField(null=True, blank=True)
	assigned_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, related_name='tool_assignments'
			)
	
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['-assignment_start']
		verbose_name = 'Tool Assignment'
		verbose_name_plural = 'Tool Assignments'
	
	def __str__(self):
		return f"{self.tool_plant.asset_number} -> {self.work_package.code}"