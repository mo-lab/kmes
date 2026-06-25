from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Project(models.Model):
	"""Top-level project entity."""
	
	class Status(models.TextChoices):
		INITIATION = 'INIT', 'Initiation'
		PLANNING = 'PLAN', 'Planning'
		EXECUTION = 'EXEC', 'Execution'
		COMMISSIONING = 'COMM', 'Commissioning'
		CLOSED = 'CLSD', 'Closed'
	
	name = models.CharField(max_length=255)
	code = models.CharField(max_length=50, unique=True, help_text="Short code, e.g., 'CU-PH2'")
	location = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	start_date = models.DateField()
	target_completion_date = models.DateField()
	actual_completion_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=4, choices=Status.choices, default=Status.INITIATION)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-start_date']
		verbose_name = 'Project'
		verbose_name_plural = 'Projects'
	
	def __str__(self):
		return f"{self.code} - {self.name}"


class Area(models.Model):
	"""Physical/logical zone within a project."""
	
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='areas')
	code = models.CharField(max_length=50)
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		unique_together = ['project', 'code']
		ordering = ['code']
		verbose_name = 'Area'
		verbose_name_plural = 'Areas'
	
	def __str__(self):
		return f"{self.code} - {self.name}"


class System(models.Model):
	"""Functional system that spans areas (e.g., Lubrication System)."""
	
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='systems')
	code = models.CharField(max_length=50)
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		unique_together = ['project', 'code']
		ordering = ['code']
		verbose_name = 'System'
		verbose_name_plural = 'Systems'
	
	def __str__(self):
		return f"{self.code} - {self.name}"


class EquipmentTag(models.Model):
	"""Central entity for all physical assets. Supports assembly hierarchy via self-referencing."""
	
	class EquipmentType(models.TextChoices):
		CRUSHER = 'CRUSH', 'Crusher'
		CONVEYOR = 'CONV', 'Conveyor'
		FLOTATION = 'FLOT', 'Flotation Cell'
		PUMP = 'PUMP', 'Pump'
		MOTOR = 'MOTOR', 'Motor'
		INSTRUMENT = 'INST', 'Instrument'
		CABLE = 'CABLE', 'Cable'
		TRANSFORMER = 'XFMR', 'Transformer'
		VALVE = 'VALV', 'Valve'
		TANK = 'TANK', 'Tank'
		SCREEN = 'SCRN', 'Screen'
		FEEDER = 'FEED', 'Feeder'
		CYCLONE = 'CYCL', 'Cyclone'
		THICKENER = 'THCK', 'Thickener'
		FILTER = 'FILT', 'Filter'
		COMPRESSOR = 'COMP', 'Compressor'
		OTHER = 'OTHR', 'Other'
	
	class Discipline(models.TextChoices):
		MECHANICAL = 'MECH', 'Mechanical'
		ELECTRICAL = 'ELEC', 'Electrical'
		PIPING = 'PIPE', 'Piping'
		INSTRUMENTATION = 'INSTR', 'Instrumentation'
		CIVIL = 'CIVL', 'Civil'
		STRUCTURAL = 'STRU', 'Structural'
	
	class Criticality(models.TextChoices):
		HIGH = 'HIGH', 'High'
		MEDIUM = 'MED', 'Medium'
		LOW = 'LOW', 'Low'
	
	class Status(models.TextChoices):
		ENGINEERING = 'ENG', 'Engineering'
		PROCURED = 'PROC', 'Procured'
		DELIVERED = 'DLVD', 'Delivered'
		INSTALLED = 'INST', 'Installed'
		ALIGNED = 'ALGN', 'Aligned'
		PRECOMM = 'PREC', 'Pre-Commissioned'
		COMMISSIONED = 'COMM', 'Commissioned'
		HANDED_OVER = 'HNDO', 'Handed Over'
		DEFECT = 'DEF', 'Defective'
	
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='equipment_tags')
	area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment_tags')
	system = models.ForeignKey(System, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment_tags')
	parent_tag = models.ForeignKey(
			'self', on_delete=models.CASCADE, null=True, blank=True,
			related_name='child_tags'
			)
	
	tag_number = models.CharField(max_length=100, db_index=True)
	description = models.CharField(max_length=500)
	equipment_type = models.CharField(max_length=5, choices=EquipmentType.choices)
	discipline = models.CharField(max_length=5, choices=Discipline.choices)
	
	manufacturer = models.CharField(max_length=255, blank=True)
	model_number = models.CharField(max_length=100, blank=True)
	serial_number = models.CharField(max_length=100, blank=True)
	criticality = models.CharField(max_length=4, choices=Criticality.choices, default=Criticality.MEDIUM)
	status = models.CharField(max_length=4, choices=Status.choices, default=Status.ENGINEERING)
	
	installation_date = models.DateField(null=True, blank=True)
	weight_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	dimensions = models.CharField(
			max_length=200, blank=True,
			help_text="LxWxH in mm, e.g., '3000x2000x1500'"
			)
	notes = models.TextField(blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['tag_number']
		indexes = [
				models.Index(fields=['project', 'tag_number']),
				models.Index(fields=['project', 'status']),
				models.Index(fields=['parent_tag']),
				]
		verbose_name = 'Equipment Tag'
		verbose_name_plural = 'Equipment Tags'
	
	def __str__(self):
		return f"{self.tag_number} - {self.description[:50]}"
	
	def get_hierarchy_tree(self, level=0):
		"""Returns a nested representation of the assembly hierarchy."""
		tree = {
				'tag': self,
				'level': level,
				'children': []
				}
		for child in self.child_tags.all():
			tree['children'].append(child.get_hierarchy_tree(level + 1))
		return tree
	
	@property
	def full_path(self):
		"""Returns full tag path like AREA/SUBAREA/TAG"""
		parts = []
		current = self
		while current:
			parts.insert(0, current.tag_number)
			current = current.parent_tag
		return '/'.join(parts)