from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Supplier(models.Model):
	"""Vendor/supplier of equipment, materials, or services."""
	
	name = models.CharField(max_length=255)
	code = models.CharField(max_length=50, unique=True, blank=True, null=True)
	contact_person = models.CharField(max_length=255, blank=True)
	email = models.EmailField(blank=True)
	phone = models.CharField(max_length=50, blank=True)
	address = models.TextField(blank=True)
	website = models.URLField(blank=True)
	
	performance_rating = models.PositiveSmallIntegerField(
			null=True, blank=True,
			help_text="Rating from 1-5",
			choices=[(i, str(i)) for i in range(1, 6)]
			)
	is_active = models.BooleanField(default=True)
	notes = models.TextField(blank=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['name']
		verbose_name = 'Supplier'
		verbose_name_plural = 'Suppliers'
	
	def __str__(self):
		return self.name


class PurchaseOrder(models.Model):
	"""Purchase order issued to a supplier."""
	
	class Status(models.TextChoices):
		DRAFT = 'DRAFT', 'Draft'
		ISSUED = 'ISSU', 'Issued'
		ACKNOWLEDGED = 'ACKN', 'Acknowledged'
		PARTIALLY_RECEIVED = 'PREC', 'Partially Received'
		COMPLETE = 'COMP', 'Complete'
		CANCELLED = 'CANC', 'Cancelled'
	
	project = models.ForeignKey(
			'core.Project', on_delete=models.CASCADE, related_name='purchase_orders'
			)
	po_number = models.CharField(max_length=100)
	supplier = models.ForeignKey(
			Supplier, on_delete=models.PROTECT, related_name='purchase_orders'
			)
	
	issue_date = models.DateField()
	expected_delivery_date = models.DateField(null=True, blank=True)
	currency = models.CharField(max_length=3, default='USD')
	total_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
	status = models.CharField(max_length=4, choices=Status.choices, default=Status.DRAFT)
	
	incoterms = models.CharField(max_length=50, blank=True, help_text="e.g., 'FOB', 'CIF', 'EXW'")
	shipping_method = models.CharField(max_length=100, blank=True)
	payment_terms = models.TextField(blank=True)
	notes = models.TextField(blank=True)
	
	created_by = models.ForeignKey(
			User, on_delete=models.SET_NULL, null=True, related_name='created_pos'
			)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-issue_date']
		verbose_name = 'Purchase Order'
		verbose_name_plural = 'Purchase Orders'
	
	def __str__(self):
		return f"PO: {self.po_number} - {self.supplier.name}"


class PurchaseOrderItem(models.Model):
	"""Line item within a purchase order."""
	
	purchase_order = models.ForeignKey(
			PurchaseOrder, on_delete=models.CASCADE, related_name='items'
			)
	equipment_tag = models.ForeignKey(
			'core.EquipmentTag', on_delete=models.SET_NULL, null=True, blank=True,
			related_name='purchase_orders'
			)
	line_item_number = models.PositiveIntegerField()
	
	description = models.CharField(max_length=500)
	quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2, default=1)
	unit = models.CharField(max_length=20, default='EA', help_text="EA, M, KG, LOT")
	unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	total_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	
	required_on_site_date = models.DateField(null=True, blank=True)
	actual_delivery_date = models.DateField(null=True, blank=True)
	is_received = models.BooleanField(default=False)
	
	notes = models.TextField(blank=True)
	
	class Meta:
		unique_together = ['purchase_order', 'line_item_number']
		ordering = ['purchase_order', 'line_item_number']
		verbose_name = 'Purchase Order Item'
		verbose_name_plural = 'Purchase Order Items'
	
	def __str__(self):
		return f"PO {self.purchase_order.po_number} - Item {self.line_item_number}: {self.description[:80]}"


class Shipment(models.Model):
	"""Shipment tracking from supplier to site."""
	
	supplier = models.ForeignKey(
			Supplier, on_delete=models.PROTECT, related_name='shipments'
			)
	shipment_number = models.CharField(max_length=100)
	
	carrier = models.CharField(max_length=255, blank=True)
	tracking_number = models.CharField(max_length=100, blank=True)
	bill_of_lading = models.CharField(max_length=100, blank=True)
	
	estimated_departure_date = models.DateField(null=True, blank=True)
	actual_departure_date = models.DateField(null=True, blank=True)
	estimated_arrival_date = models.DateField(null=True, blank=True)
	actual_arrival_date = models.DateField(null=True, blank=True)
	
	port_of_origin = models.CharField(max_length=255, blank=True)
	port_of_destination = models.CharField(max_length=255, blank=True)
	customs_cleared_date = models.DateField(null=True, blank=True)
	
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-estimated_arrival_date']
		verbose_name = 'Shipment'
		verbose_name_plural = 'Shipments'
	
	def __str__(self):
		return f"Shipment: {self.shipment_number} - {self.supplier.name}"


class ShipmentItem(models.Model):
	"""Individual items within a shipment."""
	
	shipment = models.ForeignKey(
			Shipment, on_delete=models.CASCADE, related_name='items'
			)
	purchase_order_item = models.ForeignKey(
			PurchaseOrderItem, on_delete=models.CASCADE, related_name='shipments'
			)
	
	quantity_shipped = models.DecimalField(max_digits=10, decimal_places=2)
	received_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	is_received = models.BooleanField(default=False)
	
	packing_list_number = models.CharField(max_length=100, blank=True)
	condition_on_arrival = models.CharField(
			max_length=50, blank=True,
			help_text="e.g., 'Good', 'Damaged', 'Incomplete'"
			)
	
	notes = models.TextField(blank=True)
	
	class Meta:
		verbose_name = 'Shipment Item'
		verbose_name_plural = 'Shipment Items'
	
	def __str__(self):
		return f"{self.shipment.shipment_number} - {self.purchase_order_item}"