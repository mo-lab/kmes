from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class CommissioningSystem(models.Model):
	"""Commissioning phase for a functional system."""
	
	class Status(models.TextChoices):
		PRECOMMISSIONING = 'PREC', 'Pre-Commissioning'
		COLD_COMMISSIONING = 'COLD', 'Cold Commissioning'
		HOT_COMMISSIONING = 'HOT', 'Hot Commissioning'
		RAMP_UP = 'RAMP', 'Ramp-Up'
		PERFORMANCE_TEST = 'PERF', 'Performance Test'
		HANDED_OVER = 'HNDO', 'Handed Over'
	
	system = models.ForeignKey(
			'core.System', on_delete=models.CASCADE, related_name='commissioning_phases'
			)
	status = models.CharField(
			max_length=4, choices=Status.choices, default=Status.PRECOMMISSIONING
			)
	
	planned_start = models.DateField()
	planned_finish = models.DateField()
	actual_start = models.DateField(null=True, blank=True)
	actual_finish = models.DateField(null=True, blank=True)
	
	lead_engineer = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='led_commissioning'
			)
	notes = models.TextField(blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		verbose_name = 'Commissioning System'
		verbose_name_plural = 'Commissioning Systems'
	
	def __str__(self):
		return f"Commissioning: {self.system.code} - {self.get_status_display()}"


class TestProcedure(models.Model):
	"""A test procedure within a commissioning system."""
	
	class TestType(models.TextChoices):
		PRECOMM = 'PREC', 'Pre-Commissioning Test'
		COLD = 'COLD', 'Cold Commissioning Test'
		HOT = 'HOT', 'Hot Commissioning Test'
		PERFORMANCE = 'PERF', 'Performance Test'
		FUNCTIONAL = 'FUNC', 'Functional Test'
		SAFETY = 'SAFE', 'Safety System Test'
	
	commissioning_system = models.ForeignKey(
			CommissioningSystem, on_delete=models.CASCADE, related_name='test_procedures'
			)
	code = models.CharField(max_length=50)
	description = models.CharField(max_length=500)
	test_type = models.CharField(max_length=4, choices=TestType.choices)
	
	procedure_document = models.ForeignKey(
			'documents.Document', on_delete=models.SET_NULL, null=True, blank=True,
			related_name='test_procedures'
			)
	
	prerequisites = models.ManyToManyField(
			'self', symmetrical=False, blank=True,
			help_text="Test procedures that must be completed before this one"
			)
	equipment_tags = models.ManyToManyField(
			'core.EquipmentTag', blank=True, related_name='test_procedures'
			)
	
	duration_hours = models.DecimalField(
			max_digits=6, decimal_places=2, null=True, blank=True
			)
	is_mandatory = models.BooleanField(default=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['code']
		verbose_name = 'Test Procedure'
		verbose_name_plural = 'Test Procedures'
	
	def __str__(self):
		return f"{self.code} - {self.description[:80]}"


class TestRecord(models.Model):
	"""A recorded execution of a test procedure."""
	
	class Result(models.TextChoices):
		PASS = 'PASS', 'Pass'
		CONDITIONAL_PASS = 'COND', 'Conditional Pass'
		FAIL = 'FAIL', 'Fail'
		IN_PROGRESS = 'IPRO', 'In Progress'
	
	test_procedure = models.ForeignKey(
			TestProcedure, on_delete=models.CASCADE, related_name='test_records'
			)
	test_number = models.PositiveIntegerField(default=1, help_text="Attempt number")
	
	executed_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, related_name='executed_tests'
			)
	witnessed_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='witnessed_tests'
			)
	
	start_datetime = models.DateTimeField()
	end_datetime = models.DateTimeField(null=True, blank=True)
	
	result = models.CharField(
			max_length=4, choices=Result.choices, default=Result.IN_PROGRESS
			)
	comments = models.TextField(blank=True)
	
	signature = models.ImageField(
			upload_to='test_signatures/%Y/%m/%d/', null=True, blank=True
			)
	witnessed_signature = models.ImageField(
			upload_to='test_signatures/%Y/%m/%d/', null=True, blank=True
			)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-start_datetime']
		verbose_name = 'Test Record'
		verbose_name_plural = 'Test Records'
	
	def __str__(self):
		return f"Record: {self.test_procedure.code} - Attempt {self.test_number} - {self.result}"


class PunchItem(models.Model):
	"""A defect or outstanding work item that must be completed before handover."""
	
	class Category(models.TextChoices):
		A_CRITICAL = 'A', 'A - Critical (Safety/Operations)'
		B_REQUIRED = 'B', 'B - Required before Handover'
		C_COSMETIC = 'C', 'C - Cosmetic/Minor'
	
	class Status(models.TextChoices):
		OPEN = 'OPEN', 'Open'
		IN_PROGRESS = 'IPRO', 'In Progress'
		RESOLVED = 'RESL', 'Resolved'
		VERIFIED_CLOSED = 'CLSD', 'Verified Closed'
		REJECTED = 'REJ', 'Rejected'
	
	project = models.ForeignKey(
			'core.Project', on_delete=models.CASCADE, related_name='punch_items'
			)
	equipment_tag = models.ForeignKey(
			'core.EquipmentTag', on_delete=models.CASCADE, null=True, blank=True,
			related_name='punch_items'
			)
	system = models.ForeignKey(
			'core.System', on_delete=models.SET_NULL, null=True, blank=True,
			related_name='punch_items'
			)
	test_record = models.ForeignKey(
			TestRecord, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='punch_items'
			)
	
	punch_number = models.CharField(max_length=50, unique=True)
	description = models.TextField()
	
	raised_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, related_name='raised_punch_items'
			)
	raised_date = models.DateField(default=timezone.now)
	
	category = models.CharField(
			max_length=1, choices=Category.choices, default=Category.B_REQUIRED
			)
	assigned_to_contractor = models.CharField(max_length=255, blank=True)
	assigned_to = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='assigned_punch_items'
			)
	
	due_date = models.DateField(null=True, blank=True)
	resolved_date = models.DateField(null=True, blank=True)
	verified_date = models.DateField(null=True, blank=True)
	verified_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='verified_punch_items'
			)
	
	status = models.CharField(max_length=4, choices=Status.choices, default=Status.OPEN)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['category', '-raised_date']
		verbose_name = 'Punch Item'
		verbose_name_plural = 'Punch Items'
	
	def __str__(self):
		return f"Punch {self.punch_number}: {self.description[:80]}"
	
	@property
	def is_overdue(self):
		if self.due_date and self.status in [self.Status.OPEN, self.Status.IN_PROGRESS]:
			return timezone.now().date() > self.due_date
		return False


class PunchItemPhoto(models.Model):
	"""Before/after photos for punch items."""
	
	punch_item = models.ForeignKey(
			PunchItem, on_delete=models.CASCADE, related_name='photos'
			)
	photo = models.ImageField(upload_to='punch_photos/%Y/%m/%d/')
	photo_type = models.CharField(
			max_length=10,
			choices=[('BEFORE', 'Before'), ('AFTER', 'After')],
			default='BEFORE'
			)
	caption = models.CharField(max_length=255, blank=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		verbose_name = 'Punch Item Photo'
		verbose_name_plural = 'Punch Item Photos'