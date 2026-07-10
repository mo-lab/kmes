from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, Shipment, ShipmentItem

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
	list_display = ['name', 'code', 'contact_person', 'email', 'performance_rating', 'is_active']
	search_fields = ['name', 'code']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
	list_display = ['po_number', 'supplier', 'project', 'issue_date', 'status', 'total_value']
	list_filter = ['status', 'project']
	search_fields = ['po_number', 'supplier__name']

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
	list_display = ['purchase_order', 'line_item_number', 'description', 'quantity_ordered', 'is_received']
	list_filter = ['is_received']
	search_fields = ['description', 'purchase_order__po_number']

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
	list_display = ['shipment_number', 'supplier', 'estimated_arrival_date', 'actual_arrival_date']
	search_fields = ['shipment_number', 'tracking_number']

@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
	list_display = ['shipment', 'purchase_order_item', 'quantity_shipped', 'is_received']
	list_filter = ['is_received']