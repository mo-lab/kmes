from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
import os


User = get_user_model()


class ProfileSettings(models.Model):
	class Language(models.TextChoices):
		farsi = 'Farsi', 'فارسی'
		english = 'Enlish', 'english'
	
	language = models.CharField(choices=Language.choices, default=Language.farsi, max_length=50)
	
	def __str__(self):
		return self.language
	
	class Meta:
		verbose_name = 'Profile Settings'
		verbose_name_plural = 'Profiles Settings'


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


class PackingList(models.Model):
	name=models.CharField(max_length=255,null=True,blank=True)
	description=models.CharField(max_length=255,null=True,blank=True)
	packing_list_num = models.CharField(max_length=100, blank=True, null=True)
	qr_code = models.ImageField(
			upload_to='packing_list_qr_codes/',
			null=True,
			blank=True,
			help_text="QR code for this packing list"
			)
	qr_code_generated_at = models.DateTimeField(null=True, blank=True)
	
	def generate_qr_code(self):
		
		from django.urls import reverse
		from django.utils import timezone
		
		# Build the URL that the QR code will point to
		# You can customize this URL based on your domain
		tag_url = f"http://127.0.0.1:8080{reverse('core:equipment_tag_detail', kwargs={'pk': self.pk})}"
		
		# Create QR code instance
		qr = qrcode.QRCode(
				version=1,
				error_correction=qrcode.constants.ERROR_CORRECT_H,
				box_size=10,
				border=4,
				)
		
		# Add data
		qr.add_data(tag_url)
		qr.make(fit=True)
		
		# Create image
		qr_image = qr.make_image(fill_color="black", back_color="white")
		
		# Save to BytesIO
		buffer = BytesIO()
		qr_image.save(buffer, format='PNG')
		
		# Save to ImageField
		filename = f'qr_{self.tag_number}.png'
		self.qr_code.save(
				filename,
				ContentFile(buffer.getvalue()),
				save=False
				)
		self.qr_code_generated_at = timezone.now()
		self.save(update_fields=['qr_code', 'qr_code_generated_at'])
		
		return self.qr_code
	
	def __str__(self):
		return f"{self.packing_list_num}"
	
	
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


class EquipmentLocation(models.Model):
	"""
	GPS location data for equipment tags.
	Each equipment tag can have one or more location records to track movement.
	"""
	
	class LocationType(models.TextChoices):
		STORAGE = 'STORE', 'Storage/Warehouse'
		INSTALLATION = 'INST', 'Installation Site'
		WORKSHOP = 'WORK', 'Workshop'
		TRANSIT = 'TRANS', 'In Transit'
		TEMPORARY = 'TEMP', 'Temporary Location'
		OTHER = 'OTHER', 'Other'
	
	equipment_tag = models.ForeignKey(
			'EquipmentTag',
			on_delete=models.CASCADE,
			related_name='locations'
			)
	
	# Location type
	location_type = models.CharField(
			max_length=5,
			choices=LocationType.choices,
			default=LocationType.INSTALLATION
			)
	
	# GPS Coordinates
	latitude = models.DecimalField(
			max_digits=9,
			decimal_places=6,
			validators=[
					MinValueValidator(-90),
					MaxValueValidator(90)
					],
			help_text="Latitude in decimal degrees (e.g., -23.550520)"
			)
	longitude = models.DecimalField(
			max_digits=9,
			decimal_places=6,
			validators=[
					MinValueValidator(-180),
					MaxValueValidator(180)
					],
			help_text="Longitude in decimal degrees (e.g., -46.633308)"
			)
	elevation = models.DecimalField(
			max_digits=8,
			decimal_places=2,
			null=True,
			blank=True,
			help_text="Elevation in meters above sea level"
			)
	
	# Accuracy
	accuracy = models.DecimalField(
			max_digits=6,
			decimal_places=2,
			null=True,
			blank=True,
			help_text="GPS accuracy in meters"
			)
	
	# Physical location description
	area = models.ForeignKey(
			'Area',
			on_delete=models.SET_NULL,
			null=True,
			blank=True,
			related_name='equipment_locations'
			)
	building = models.CharField(max_length=100, blank=True, help_text="Building or structure name")
	floor = models.CharField(max_length=50, blank=True, help_text="Floor level")
	room = models.CharField(max_length=50, blank=True, help_text="Room number or name")
	grid_reference = models.CharField(max_length=50, blank=True, help_text="Site grid reference")
	
	# Address
	address = models.TextField(blank=True, help_text="Physical address or description")
	city = models.CharField(max_length=100, blank=True)
	state = models.CharField(max_length=100, blank=True)
	country = models.CharField(max_length=100, blank=True)
	postal_code = models.CharField(max_length=20, blank=True)
	
	# Status
	is_current = models.BooleanField(
			default=True,
			help_text="Is this the current location of the equipment?"
			)
	is_verified = models.BooleanField(
			default=False,
			help_text="Has this location been verified?"
			)
	
	# Dates
	arrival_date = models.DateTimeField(
			default=timezone.now,
			help_text="When the equipment arrived at this location"
			)
	departure_date = models.DateTimeField(
			null=True,
			blank=True,
			help_text="When the equipment left this location"
			)
	
	# User who recorded this location
	recorded_by = models.ForeignKey(
			'auth.User',
			on_delete=models.SET_NULL,
			null=True,
			blank=True,
			related_name='recorded_locations'
			)
	
	# Verification
	verified_by = models.ForeignKey(
			'auth.User',
			on_delete=models.SET_NULL,
			null=True,
			blank=True,
			related_name='verified_locations'
			)
	verified_date = models.DateTimeField(null=True, blank=True)
	
	# Notes
	notes = models.TextField(blank=True)
	
	# Metadata
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-arrival_date']
		verbose_name = 'Equipment Location'
		verbose_name_plural = 'Equipment Locations'
		indexes = [
				models.Index(fields=['equipment_tag', 'is_current']),
				models.Index(fields=['latitude', 'longitude']),
				models.Index(fields=['location_type']),
				]
	
	def __str__(self):
		return f"{self.equipment_tag.tag_number} - {self.get_location_type_display()} ({self.latitude}, {self.longitude})"
	
	@property
	def coordinates(self):
		"""Return coordinates as a tuple."""
		return (float(self.latitude), float(self.longitude))
	
	@property
	def google_maps_url(self):
		"""Generate Google Maps URL for this location."""
		return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
	
	@property
	def openstreetmap_url(self):
		"""Generate OpenStreetMap URL for this location."""
		return f"https://www.openstreetmap.org/?mlat={self.latitude}&mlon={self.longitude}&zoom=18"
	
	def save(self, *args, **kwargs):
		# If this is marked as current, unmark other current locations for this equipment
		if self.is_current:
			EquipmentLocation.objects.filter(
					equipment_tag=self.equipment_tag,
					is_current=True
					).exclude(pk=self.pk).update(is_current=False)
		
		super().save(*args, **kwargs)


class EquipmentLocationImage(models.Model):
	"""
	Images associated with equipment locations.
	Each location can have multiple images.
	"""
	
	class ImageType(models.TextChoices):
		GENERAL = 'GEN', 'General View'
		CLOSEUP = 'CLOSE', 'Close-up'
		SURROUNDING = 'SURR', 'Surrounding Area'
		INSTALLATION = 'INST', 'Installation Detail'
		DAMAGE = 'DAMG', 'Damage/Deterioration'
		GPS = 'GPS', 'GPS Screenshot'
		SURVEY = 'SURV', 'Survey Mark'
		OTHER = 'OTHER', 'Other'
	
	location = models.ForeignKey(
			EquipmentLocation,
			on_delete=models.CASCADE,
			related_name='images'
			)
	
	# Image file
	image = models.ImageField(
			upload_to='equipment_locations/%Y/%m/%d/',
			help_text="Photo of the equipment at this location"
			)
	
	# Image metadata
	title = models.CharField(max_length=200, blank=True)
	description = models.TextField(blank=True)
	image_type = models.CharField(
			max_length=5,
			choices=ImageType.choices,
			default=ImageType.GENERAL
			)
	
	# Date photo was taken
	taken_date = models.DateTimeField(
			null=True,
			blank=True,
			help_text="When the photo was taken"
			)
	
	# Direction the photo was taken from
	direction = models.DecimalField(
			max_digits=5,
			decimal_places=1,
			null=True,
			blank=True,
			validators=[
					MinValueValidator(0),
					MaxValueValidator(360)
					],
			help_text="Compass direction in degrees (0-360)"
			)
	
	# Is this the primary image for the location?
	is_primary = models.BooleanField(default=False)
	
	# Upload info
	uploaded_by = models.ForeignKey(
			'auth.User',
			on_delete=models.SET_NULL,
			null=True,
			blank=True,
			related_name='uploaded_location_images'
			)
	
	# File metadata
	file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")
	width = models.PositiveIntegerField(null=True, blank=True, help_text="Image width in pixels")
	height = models.PositiveIntegerField(null=True, blank=True, help_text="Image height in pixels")
	
	# Metadata
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-is_primary', '-created_at']
		verbose_name = 'Equipment Location Image'
		verbose_name_plural = 'Equipment Location Images'
	
	def __str__(self):
		return f"Image for {self.location.equipment_tag.tag_number} - {self.get_image_type_display()}"
	
	def save(self, *args, **kwargs):
		# If marked as primary, unmark other primary images for this location
		if self.is_primary:
			EquipmentLocationImage.objects.filter(
					location=self.location,
					is_primary=True
					).exclude(pk=self.pk).update(is_primary=False)
		
		# Get image dimensions if not set
		if self.image and not self.width:
			try:
				from PIL import Image
				img = Image.open(self.image)
				self.width, self.height = img.size
			except:
				pass
		
		# Get file size if not set
		if self.image and not self.file_size:
			try:
				self.file_size = self.image.size
			except:
				pass
		
		super().save(*args, **kwargs)
	
	@property
	def thumbnail_url(self):
		"""Return URL for thumbnail version if you implement thumbnails."""
		return self.image.url
	
	@property
	def image_dimensions(self):
		"""Return image dimensions as string."""
		if self.width and self.height:
			return f"{self.width}x{self.height}"
		return "Unknown"


	
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
		CRANE = 'CR', 'Crane'
		SCREW_WASHER_NUT = 'SCNW', 'Screw Nut Washer'
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
	
	installation_order = models.IntegerField(default=0, blank=True, null=True)
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='equipment_tags',null=True,blank=True)
	area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment_tags')
	system = models.ForeignKey(System, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment_tags')
	parent_tag = models.ForeignKey(
			'self', on_delete=models.CASCADE, null=True, blank=True,
			related_name='child_tags'
			)
	drawing_num = models.CharField(max_length=100, blank=True, null=True)
	tag_number = models.CharField(max_length=100, db_index=True)
	description = models.CharField(max_length=500,null=True,blank=True)
	equipment_type = models.CharField(max_length=5, choices=EquipmentType.choices,null=True,blank=True)
	discipline = models.CharField(max_length=5, choices=Discipline.choices,null=True,blank=True)
	packing = models.ForeignKey(PackingList, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment_tags')
	
	manufacturer = models.CharField(max_length=255, blank=True)
	model_number = models.CharField(max_length=100, blank=True)
	serial_number = models.CharField(max_length=100, blank=True)
	criticality = models.CharField(max_length=4, choices=Criticality.choices, default=Criticality.MEDIUM)
	status = models.CharField(max_length=4, choices=Status.choices, default=Status.ENGINEERING)
	
	installation_date = models.DateField(null=True, blank=True)
	weight_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
	dimensions = models.CharField(
			max_length=200, blank=True,
			help_text="LxWxH in mm, e.g., '3000x2000x1500'"
			)
	notes = models.TextField(blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	qr_code = models.ImageField(
			upload_to='equipment_qr_codes/',
			null=True,
			blank=True,
			help_text="QR code for this equipment tag"
			)
	qr_code_generated_at = models.DateTimeField(null=True, blank=True)
	
	def generate_qr_code(self):
		
		from django.urls import reverse
		from django.utils import timezone
		
		# Build the URL that the QR code will point to
		# You can customize this URL based on your domain
		tag_url = f"http://0.0.0.0:8080{reverse('core:equipment_tag_detail', kwargs={'pk': self.pk})}"
		
		# Create QR code instance
		qr = qrcode.QRCode(
				version=1,
				error_correction=qrcode.constants.ERROR_CORRECT_H,
				box_size=10,
				border=4,
				)
		
		# Add data
		qr.add_data(tag_url)
		qr.make(fit=True)
		
		# Create image
		qr_image = qr.make_image(fill_color="black", back_color="white")
		
		# Save to BytesIO
		buffer = BytesIO()
		qr_image.save(buffer, format='PNG')
		
		# Save to ImageField
		filename = f'qr_{self.tag_number}.png'
		self.qr_code.save(
				filename,
				ContentFile(buffer.getvalue()),
				save=False
				)
		self.qr_code_generated_at = timezone.now()
		self.save(update_fields=['qr_code', 'qr_code_generated_at'])
		
		return self.qr_code
	
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
	
	def save(self, *args, **kwargs):
		is_new = self.pk is None
		super().save(*args, **kwargs)
		
		# Auto-generate QR code for new tags
		if is_new and not self.qr_code:
			self.generate_qr_code()
	
	def get_hierarchy_tree(self, level=0):
		"""Returns a nested representation of the assembly hierarchy."""
		tree = {
				'tag':      self,
				'level':    level,
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
	
	@property
	def current_location(self):
		"""Get the current location of this equipment."""
		return self.locations.filter(is_current=True).first()
	
	@property
	def location_history(self):
		"""Get location history for this equipment."""
		return self.locations.filter(is_current=False).order_by('-arrival_date')
	
	def set_location(self, latitude, longitude, location_type='INST', **kwargs):
		"""Set a new current location for this equipment."""
		# Mark old locations as not current
		self.locations.filter(is_current=True).update(
				is_current=False,
				departure_date=timezone.now()
				)
		
		# Create new location
		return EquipmentLocation.objects.create(
				equipment_tag=self,
				latitude=latitude,
				longitude=longitude,
				location_type=location_type,
				is_current=True,
				**kwargs
				)


class Drawing(models.Model):
	name = models.CharField(null=True, blank=True, max_length=200)
	url = models.CharField(null=True, blank=True)
	width = models.IntegerField(null=True, blank=True, default=6000)
	height = models.IntegerField(null=True, blank=True, default=4242)
	
	def __str__(self):
		return self.name


class DrawingHotSpot(models.Model):
	drawing = models.ForeignKey(Drawing, on_delete=models.CASCADE, null=True, blank=True, related_name='hot_spots')
	top = models.IntegerField(null=True, blank=True)
	left = models.IntegerField(null=True, blank=True)
	width = models.IntegerField(null=True, blank=True, default=192)
	height = models.IntegerField(null=True, blank=True, default=35)
	equipment_tag_ID = models.IntegerField(null=True, blank=True)


class PackingListItem(models.Model):
	equipment_tag=models.ForeignKey(EquipmentTag, on_delete=models.SET_NULL,related_name='packing_list_items', blank=True, null=True)
	packing_list=models.ForeignKey(PackingList, on_delete=models.SET_NULL, blank=True, null=True,related_name='packing_list_items')
	received_date=models.DateField(null=True, blank=True)
	discipline=models.CharField(max_length=255, null=True, blank=True)
	page_no=models.IntegerField(null=True, blank=True)
	goods_item_no=models.CharField(max_length=255, null=True, blank=True)
	type_of_material=models.CharField(max_length=255, null=True, blank=True)
	material_description=models.CharField(max_length=255, null=True, blank=True)
	vendor=models.CharField(max_length=255, null=True, blank=True)
	mrs_no=models.CharField(max_length=255, null=True, blank=True)
	mrs_date=models.DateField(null=True, blank=True)
	qty_opi=models.IntegerField(null=True, blank=True)
	miv=models.IntegerField(null=True, blank=True)
	total_weight_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)


class EquipmentGrid(models.Model):
	grid_x=models.CharField(max_length=255, null=True, blank=True)
	grid_y=models.CharField(max_length=255, null=True, blank=True)
	grid_z=models.CharField(max_length=255, null=True, blank=True)
	equipment_tag=models.ForeignKey(EquipmentTag, on_delete=models.CASCADE,related_name='grids', blank=True, null=True)
	
	def __str__(self):
		if self.grid_z and self.grid_x and self.grid_y:
			return f'{self.grid_x} - {self.grid_y} - {self.grid_z}'
	