from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()


class Document(models.Model):
	"""Any project document: drawings, datasheets, manuals, etc."""
	
	class DocType(models.TextChoices):
		DRAWING = 'DWG', 'Drawing'
		P_AND_ID = 'PNID', 'P&ID'
		DATASHEET = 'DATA', 'Datasheet'
		MANUAL = 'MAN', 'Manual'
		PROCEDURE = 'PROC', 'Procedure'
		SPECIFICATION = 'SPEC', 'Specification'
		CERTIFICATE = 'CERT', 'Certificate'
		REPORT = 'RPT', 'Report'
		CALCULATION = 'CALC', 'Calculation'
		OTHER = 'OTHR', 'Other'
	
	class DocStatus(models.TextChoices):
		DRAFT = 'DRAFT', 'Draft'
		UNDER_REVIEW = 'REVW', 'Under Review'
		APPROVED = 'APPR', 'Approved'
		ISSUED_FOR_CONSTRUCTION = 'IFC', 'Issued for Construction'
		AS_BUILT = 'ASBL', 'As-Built'
		SUPERSEDED = 'SUPD', 'Superseded'
	
	class Discipline(models.TextChoices):
		MECHANICAL = 'MECH', 'Mechanical'
		ELECTRICAL = 'ELEC', 'Electrical'
		PIPING = 'PIPE', 'Piping'
		INSTRUMENTATION = 'INSTR', 'Instrumentation'
		CIVIL = 'CIVL', 'Civil'
		STRUCTURAL = 'STRU', 'Structural'
		PROCESS = 'PROC', 'Process'
		GENERAL = 'GEN', 'General'
	
	project = models.ForeignKey(
			'core.Project', on_delete=models.CASCADE, related_name='documents'
			)
	document_number = models.CharField(max_length=100)
	title = models.CharField(max_length=500)
	doc_type = models.CharField(max_length=5, choices=DocType.choices)
	discipline = models.CharField(max_length=5, choices=Discipline.choices)
	revision = models.CharField(max_length=20, help_text="e.g., 'Rev B', 'IFC', 'A'")
	status = models.CharField(max_length=10, choices=DocStatus.choices, default=DocStatus.DRAFT)
	
	file_upload = models.FileField(
			upload_to='documents/%Y/%m/%d/',
			validators=[
					FileExtensionValidator(
							allowed_extensions=['pdf', 'dwg', 'dxf', 'doc', 'docx', 'xls', 'xlsx', 'zip']
							)
					],
			null=True, blank=True
			)
	file_path = models.CharField(
			max_length=500, blank=True,
			help_text="Alternative path to document if not uploaded directly"
			)
	
	issue_date = models.DateField(null=True, blank=True)
	submitted_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='submitted_documents'
			)
	approved_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, blank=True,
			related_name='approved_documents'
			)
	
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['document_number', '-revision']
		verbose_name = 'Document'
		verbose_name_plural = 'Documents'
	
	def __str__(self):
		return f"{self.document_number} Rev {self.revision} - {self.title[:80]}"


class TagDocument(models.Model):
	"""Many-to-many relationship between equipment tags and documents."""
	
	equipment_tag = models.ForeignKey(
			'core.EquipmentTag', on_delete=models.CASCADE, related_name='tag_documents'
			)
	document = models.ForeignKey(
			Document, on_delete=models.CASCADE, related_name='tag_documents'
			)
	
	relation_type = models.CharField(
			max_length=50, default='references',
			help_text="e.g., 'references', 'defines', 'specifies'"
			)
	added_date = models.DateField(auto_now_add=True)
	
	class Meta:
		unique_together = ['equipment_tag', 'document']
		verbose_name = 'Tag Document Relationship'
		verbose_name_plural = 'Tag Document Relationships'
	
	def __str__(self):
		return f"{self.equipment_tag.tag_number} <-> {self.document.document_number}"