# from django.views import generic
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib import messages
# from django.shortcuts import render, redirect, get_object_or_404
# from django.urls import reverse, reverse_lazy
# from django.db import transaction
#
# from .models import (
# 	Supplier, PurchaseOrder, PurchaseOrderItem,
# 	Shipment, ShipmentItem
# 	)
# from ..core.models import Project
# from ..procurement.forms import (
# 	SupplierForm, PurchaseOrderForm, PurchaseOrderItemForm,
# 	PurchaseOrderItemInlineFormSet, ShipmentForm, ShipmentItemForm,
# 	ShipmentReceiveForm
# 	)
# from ..base_views import BaseCreateView, BaseUpdateView, BaseDeleteView
#
#
# # ============================================
# # SUPPLIER VIEWS
# # ============================================
#
# class SupplierListView(LoginRequiredMixin, generic.ListView):
# 	model = Supplier
# 	template_name = 'procurement/supplier_list.html'
# 	context_object_name = 'suppliers'
# 	paginate_by = 20
#
# 	def get_queryset(self):
# 		queryset = Supplier.objects.all()
# 		search = self.request.GET.get('search')
# 		if search:
# 			queryset = queryset.filter(name__icontains=search)
# 		return queryset
#
#
# class SupplierCreateView(BaseCreateView):
# 	model = Supplier
# 	form_class = SupplierForm
# 	template_name = 'procurement/supplier_form.html'
# 	success_message = "Supplier '%(name)s' was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:supplier_list')
#
#
# class SupplierUpdateView(BaseUpdateView):
# 	model = Supplier
# 	form_class = SupplierForm
# 	template_name = 'procurement/supplier_form.html'
# 	success_message = "Supplier '%(name)s' was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:supplier_list')
#
#
# class SupplierDeleteView(BaseDeleteView):
# 	model = Supplier
# 	template_name = 'procurement/supplier_confirm_delete.html'
# 	success_url = reverse_lazy('procurement:supplier_list')
# 	success_message = "Supplier was deleted successfully."
#
#
# # ============================================
# # PURCHASE ORDER VIEWS
# # ============================================
#
# class PurchaseOrderListView(LoginRequiredMixin, generic.ListView):
# 	model = PurchaseOrder
# 	template_name = 'procurement/purchase_order_list.html'
# 	context_object_name = 'procurement:purchase_orders'
# 	paginate_by = 20
#
# 	def get_queryset(self):
# 		queryset = PurchaseOrder.objects.select_related('project', 'supplier')
# 		project_id = self.request.GET.get('project')
# 		if project_id:
# 			queryset = queryset.filter(project_id=project_id)
# 		status = self.request.GET.get('status')
# 		if status:
# 			queryset = queryset.filter(status=status)
# 		return queryset.order_by('-issue_date')
#
#
# class PurchaseOrderDetailView(LoginRequiredMixin, generic.DetailView):
# 	model = PurchaseOrder
# 	template_name = 'procurement/purchase_order_detail.html'
# 	context_object_name = 'po'
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		context['items'] = self.object.items.select_related('equipment_tag').all()
# 		context['shipments'] = Shipment.objects.filter(
# 				items__purchase_order_item__purchase_order=self.object
# 				).distinct()
# 		return context
#
#
# class PurchaseOrderCreateView(BaseCreateView):
# 	model = PurchaseOrder
# 	form_class = PurchaseOrderForm
# 	template_name = 'procurement/purchase_order_form.html'
# 	success_message = "Purchase Order '%(po_number)s' was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:purchase_order_detail', kwargs={'pk': self.object.pk})
#
# 	def get_initial(self):
# 		initial = super().get_initial()
# 		project_id = self.kwargs.get('project_id')
# 		if project_id:
# 			initial['project'] = get_object_or_404(Project, pk=project_id)
# 		return initial
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		if self.request.POST:
# 			context['items_formset'] = PurchaseOrderItemInlineFormSet(
# 					self.request.POST, instance=self.object
# 					)
# 		else:
# 			context['items_formset'] = PurchaseOrderItemInlineFormSet(
# 					instance=self.object
# 					)
# 		return context
#
# 	def form_valid(self, form):
# 		context = self.get_context_data()
# 		items_formset = context['items_formset']
#
# 		with transaction.atomic():
# 			self.object = form.save()
# 			if items_formset.is_valid():
# 				items_formset.instance = self.object
# 				items_formset.save()
#
# 		return super().form_valid(form)
#
#
# class PurchaseOrderUpdateView(BaseUpdateView):
# 	model = PurchaseOrder
# 	form_class = PurchaseOrderForm
# 	template_name = 'procurement/purchase_order_form.html'
# 	success_message = "Purchase Order '%(po_number)s' was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('purchase_order_detail', kwargs={'pk': self.object.pk})
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		if self.request.POST:
# 			context['items_formset'] = PurchaseOrderItemInlineFormSet(
# 					self.request.POST, instance=self.object
# 					)
# 		else:
# 			context['items_formset'] = PurchaseOrderItemInlineFormSet(
# 					instance=self.object
# 					)
# 		return context
#
# 	def form_valid(self, form):
# 		context = self.get_context_data()
# 		items_formset = context['items_formset']
#
# 		with transaction.atomic():
# 			self.object = form.save()
# 			if items_formset.is_valid():
# 				items_formset.instance = self.object
# 				items_formset.save()
#
# 		return super().form_valid(form)
#
#
# class PurchaseOrderDeleteView(BaseDeleteView):
# 	model = PurchaseOrder
# 	template_name = 'procurement/purchase_order_confirm_delete.html'
# 	success_url = reverse_lazy('purchase_order_list')
# 	success_message = "Purchase Order was deleted successfully."
#
#
# # ============================================
# # PURCHASE ORDER ITEM VIEWS
# # ============================================
#
# class PurchaseOrderItemCreateView(BaseCreateView):
# 	model = PurchaseOrderItem
# 	form_class = PurchaseOrderItemForm
# 	template_name = 'procurement/purchase_order_item_form.html'
# 	success_message = "Purchase Order item was added successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:purchase_order_detail', kwargs={'pk': self.object.purchase_order.pk})
#
#
# class PurchaseOrderItemUpdateView(BaseUpdateView):
# 	model = PurchaseOrderItem
# 	form_class = PurchaseOrderItemForm
# 	template_name = 'procurement/purchase_order_item_form.html'
# 	success_message = "Purchase Order item was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:purchase_order_detail', kwargs={'pk': self.object.purchase_order.pk})
#
#
# class PurchaseOrderItemDeleteView(BaseDeleteView):
# 	model = PurchaseOrderItem
# 	template_name = 'procurement/purchase_order_item_confirm_delete.html'
# 	success_message = "Purchase Order item was deleted successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:purchase_order_detail', kwargs={'pk': self.object.purchase_order.pk})
#
#
# # ============================================
# # SHIPMENT VIEWS
# # ============================================
#
# class ShipmentDetailView(LoginRequiredMixin, generic.DetailView):
# 	model = Shipment
# 	template_name = 'procurement/shipment_detail.html'
# 	context_object_name = 'shipment'
#
# 	def get_context_data(self, **kwargs):
# 		context = super().get_context_data(**kwargs)
# 		context['items'] = self.object.items.select_related(
# 				'purchase_order_item__purchase_order'
# 				).all()
# 		return context
#
#
# class ShipmentCreateView(BaseCreateView):
# 	model = Shipment
# 	form_class = ShipmentForm
# 	template_name = 'procurement/shipment_form.html'
# 	success_message = "Shipment '%(shipment_number)s' was created successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:shipment_detail', kwargs={'pk': self.object.pk})
#
#
# class ShipmentUpdateView(BaseUpdateView):
# 	model = Shipment
# 	form_class = ShipmentForm
# 	template_name = 'procurement/shipment_form.html'
# 	success_message = "Shipment '%(shipment_number)s' was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:shipment_detail', kwargs={'pk': self.object.pk})
#
#
# class ShipmentDeleteView(BaseDeleteView):
# 	model = Shipment
# 	template_name = 'procurement/shipment_confirm_delete.html'
# 	success_url = reverse_lazy('purchase_order_list')
# 	success_message = "Shipment was deleted successfully."
#
#
# # ============================================
# # SHIPMENT ITEM VIEWS
# # ============================================
#
# class ShipmentItemCreateView(BaseCreateView):
# 	model = ShipmentItem
# 	form_class = ShipmentItemForm
# 	template_name = 'procurement/shipment_item_form.html'
# 	success_message = "Shipment item was added successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:shipment_detail', kwargs={'pk': self.object.shipment.pk})
#
#
# class ShipmentItemUpdateView(BaseUpdateView):
# 	model = ShipmentItem
# 	form_class = ShipmentItemForm
# 	template_name = 'procurement/shipment_item_form.html'
# 	success_message = "Shipment item was updated successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:shipment_detail', kwargs={'pk': self.object.shipment.pk})
#
#
# class ShipmentItemDeleteView(BaseDeleteView):
# 	model = ShipmentItem
# 	template_name = 'procurement/shipment_item_confirm_delete.html'
# 	success_message = "Shipment item was deleted successfully."
#
# 	def get_success_url(self):
# 		return reverse('procurement:shipment_detail', kwargs={'pk': self.object.shipment.pk})
#
#
# def shipment_receive_view(request, pk):
# 	"""Receive items from a shipment."""
# 	shipment = get_object_or_404(Shipment, pk=pk)
# 	items = shipment.items.all()
#
# 	if request.method == 'POST':
# 		with transaction.atomic():
# 			received_count = 0
# 			for item in items:
# 				prefix = f'item_{item.pk}'
# 				received_qty = request.POST.get(f'{prefix}_received_quantity')
# 				is_received = request.POST.get(f'{prefix}_is_received') == 'on'
# 				condition = request.POST.get(f'{prefix}_condition', 'Good')
#
# 				if is_received or received_qty:
# 					item.received_quantity = received_qty or item.quantity_shipped
# 					item.is_received = True
# 					item.condition_on_arrival = condition
# 					item.save()
#
# 					# Update PO item delivery status
# 					po_item = item.purchase_order_item
# 					if po_item.equipment_tag:
# 						po_item.equipment_tag.status = 'DLVD'
# 						po_item.equipment_tag.save()
#
# 					po_item.is_received = True
# 					po_item.actual_delivery_date = shipment.actual_arrival_date
# 					po_item.save()
#
# 					received_count += 1
#
# 			# Update purchase order status
# 			po = items.first().purchase_order_item.purchase_order if items.exists() else None
# 			if po:
# 				all_received = all(
# 						item.is_received for item in po.items.filter(shipments__isnull=False)
# 						)
# 				po.status = 'COMP' if all_received else 'PREC'
# 				po.save()
#
# 			messages.success(request, f"Successfully received {received_count} items.")
# 		return redirect('procurement:shipment_detail', pk=shipment.pk)
#
# 	return render(request, 'procurement/shipment_receive.html', {
# 			'shipment': shipment,
# 			'items': items,
# 			})
