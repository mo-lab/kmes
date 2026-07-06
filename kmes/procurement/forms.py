# from django import forms
# from django.forms import inlineformset_factory
# from ..procurement.models import (
# 	Supplier, PurchaseOrder, PurchaseOrderItem,
# 	Shipment, ShipmentItem
# 	)
# from ..core.models import EquipmentTag
#
#
# class SupplierForm(forms.ModelForm):
# 	"""Form for creating and updating suppliers."""
#
# 	class Meta:
# 		model = Supplier
# 		fields = [
# 				'name', 'code', 'contact_person', 'email',
# 				'phone', 'address', 'website', 'performance_rating',
# 				'is_active', 'notes'
# 				]
# 		widgets = {
# 				'name': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Supplier company name'
# 						}),
# 				'code': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., SUP-001'
# 						}),
# 				'contact_person': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Full name of contact person'
# 						}),
# 				'email': forms.EmailInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'contact@supplier.com'
# 						}),
# 				'phone': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': '+1 234 567 8900'
# 						}),
# 				'address': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Full address...'
# 						}),
# 				'website': forms.URLInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'https://www.supplier.com'
# 						}),
# 				'performance_rating': forms.Select(attrs={'class': 'form-select'}),
# 				'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Additional notes...'
# 						}),
# 				}
#
#
# class PurchaseOrderForm(forms.ModelForm):
# 	"""Form for creating and updating purchase orders."""
#
# 	class Meta:
# 		model = PurchaseOrder
# 		fields = [
# 				'project', 'po_number', 'supplier', 'issue_date',
# 				'expected_delivery_date', 'currency', 'total_value',
# 				'status', 'incoterms', 'shipping_method', 'payment_terms',
# 				'notes'
# 				]
# 		widgets = {
# 				'project': forms.Select(attrs={'class': 'form-select'}),
# 				'po_number': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., PO-2024-001'
# 						}),
# 				'supplier': forms.Select(attrs={'class': 'form-select'}),
# 				'issue_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'expected_delivery_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'currency': forms.Select(choices=[
# 						('USD', 'USD - US Dollar'),
# 						('EUR', 'EUR - Euro'),
# 						('GBP', 'GBP - British Pound'),
# 						('AUD', 'AUD - Australian Dollar'),
# 						('CAD', 'CAD - Canadian Dollar'),
# 						('CLP', 'CLP - Chilean Peso'),
# 						], attrs={'class': 'form-select'}),
# 				'total_value': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': '0.00',
# 						'step': '0.01'
# 						}),
# 				'status': forms.Select(attrs={'class': 'form-select'}),
# 				'incoterms': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., FOB, CIF, EXW'
# 						}),
# 				'shipping_method': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., Sea Freight, Air Freight'
# 						}),
# 				'payment_terms': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 2,
# 						'placeholder': 'e.g., 30% advance, 70% on delivery'
# 						}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Additional notes...'
# 						}),
# 				}
#
#
# class PurchaseOrderItemForm(forms.ModelForm):
# 	"""Form for purchase order line items."""
#
# 	class Meta:
# 		model = PurchaseOrderItem
# 		fields = [
# 				'equipment_tag', 'line_item_number', 'description',
# 				'quantity_ordered', 'unit', 'unit_price', 'total_price',
# 				'required_on_site_date', 'notes'
# 				]
# 		widgets = {
# 				'equipment_tag': forms.Select(attrs={'class': 'form-select'}),
# 				'line_item_number': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'min': '1'
# 						}),
# 				'description': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Item description'
# 						}),
# 				'quantity_ordered': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'min': '0',
# 						'step': '0.01'
# 						}),
# 				'unit': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'EA, M, KG, LOT'
# 						}),
# 				'unit_price': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'step': '0.01',
# 						'placeholder': '0.00'
# 						}),
# 				'total_price': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'step': '0.01',
# 						'readonly': 'readonly'
# 						}),
# 				'required_on_site_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'notes': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Additional notes'
# 						}),
# 				}
#
# 	def __init__(self, *args, **kwargs):
# 		project_id = kwargs.pop('project_id', None)
# 		super().__init__(*args, **kwargs)
#
# 		if project_id:
# 			self.fields['equipment_tag'].queryset = EquipmentTag.objects.filter(
# 					project_id=project_id
# 					)
#
#
# # Inline formset for purchase order items
# PurchaseOrderItemInlineFormSet = inlineformset_factory(
# 		PurchaseOrder,
# 		PurchaseOrderItem,
# 		form=PurchaseOrderItemForm,
# 		extra=1,
# 		can_delete=True
# 		)
#
#
# class ShipmentForm(forms.ModelForm):
# 	"""Form for creating and updating shipments."""
#
# 	class Meta:
# 		model = Shipment
# 		fields = [
# 				'supplier', 'shipment_number', 'carrier',
# 				'tracking_number', 'bill_of_lading',
# 				'estimated_departure_date', 'actual_departure_date',
# 				'estimated_arrival_date', 'actual_arrival_date',
# 				'port_of_origin', 'port_of_destination',
# 				'customs_cleared_date', 'notes'
# 				]
# 		widgets = {
# 				'supplier': forms.Select(attrs={'class': 'form-select'}),
# 				'shipment_number': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., SHIP-2024-001'
# 						}),
# 				'carrier': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., Maersk, DHL'
# 						}),
# 				'tracking_number': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Tracking/container number'
# 						}),
# 				'bill_of_lading': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'B/L number'
# 						}),
# 				'estimated_departure_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'actual_departure_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'estimated_arrival_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'actual_arrival_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'port_of_origin': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., Shanghai, China'
# 						}),
# 				'port_of_destination': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'e.g., Antofagasta, Chile'
# 						}),
# 				'customs_cleared_date': forms.DateInput(attrs={
# 						'class': 'form-control',
# 						'type': 'date'
# 						}),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 3,
# 						'placeholder': 'Additional notes...'
# 						}),
# 				}
#
#
# class ShipmentItemForm(forms.ModelForm):
# 	"""Form for shipment items."""
#
# 	class Meta:
# 		model = ShipmentItem
# 		fields = [
# 				'purchase_order_item', 'quantity_shipped',
# 				'packing_list_number', 'notes'
# 				]
# 		widgets = {
# 				'purchase_order_item': forms.Select(attrs={'class': 'form-select'}),
# 				'quantity_shipped': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'min': '0',
# 						'step': '0.01'
# 						}),
# 				'packing_list_number': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Packing list reference'
# 						}),
# 				'notes': forms.TextInput(attrs={
# 						'class': 'form-control',
# 						'placeholder': 'Additional notes'
# 						}),
# 				}
#
#
# class ShipmentReceiveForm(forms.ModelForm):
# 	"""Form for receiving shipments."""
#
# 	class Meta:
# 		model = ShipmentItem
# 		fields = [
# 				'received_quantity', 'is_received', 'condition_on_arrival', 'notes'
# 				]
# 		widgets = {
# 				'received_quantity': forms.NumberInput(attrs={
# 						'class': 'form-control',
# 						'min': '0',
# 						'step': '0.01'
# 						}),
# 				'is_received': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
# 				'condition_on_arrival': forms.Select(
# 						choices=[
# 								('Good', 'Good'),
# 								('Damaged', 'Damaged'),
# 								('Incomplete', 'Incomplete'),
# 								],
# 						attrs={'class': 'form-select'}
# 						),
# 				'notes': forms.Textarea(attrs={
# 						'class': 'form-control',
# 						'rows': 2,
# 						'placeholder': 'Receiving notes...'
# 						}),
# 				}