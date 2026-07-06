# # your_app/urls/procurement.py
# from django.urls import path
# from .views import *
#
# app_name = 'procurement'
#
# urlpatterns = [
# 		# ============================================
# 		# SUPPLIER URLS
# 		# ============================================
# 		path(
# 			'suppliers/',
# 			SupplierListView.as_view(),
# 			name='supplier_list'
# 			),
#
# 		path(
# 			'suppliers/create/',
# 			SupplierCreateView.as_view(),
# 			name='supplier_create'
# 			),
#
# 		path(
# 			'suppliers/<int:pk>/update/',
# 			SupplierUpdateView.as_view(),
# 			name='supplier_update'
# 			),
#
# 		path(
# 			'suppliers/<int:pk>/delete/',
# 			SupplierDeleteView.as_view(),
# 			name='supplier_delete'
# 			),
#
# 		# ============================================
# 		# PURCHASE ORDER URLS
# 		# ============================================
# 		path(
# 			'orders/',
# 			PurchaseOrderListView.as_view(),
# 			name='purchase_order_list'
# 			),
#
# 		path(
# 			'orders/create/',
# 			PurchaseOrderCreateView.as_view(),
# 			name='purchase_order_create'
# 			),
#
# 		path(
# 			'orders/create/project/<int:project_id>/',
# 			PurchaseOrderCreateView.as_view(),
# 			name='purchase_order_create_for_project'
# 			),
#
# 		path(
# 			'orders/<int:pk>/',
# 			PurchaseOrderDetailView.as_view(),
# 			name='purchase_order_detail'
# 			),
#
# 		path(
# 			'orders/<int:pk>/update/',
# 			PurchaseOrderUpdateView.as_view(),
# 			name='purchase_order_update'
# 			),
#
# 		path(
# 			'orders/<int:pk>/delete/',
# 			PurchaseOrderDeleteView.as_view(),
# 			name='purchase_order_delete'
# 			),
#
# 		# ============================================
# 		# PURCHASE ORDER ITEM URLS
# 		# ============================================
# 		path(
# 			'orders/<int:order_id>/items/create/',
# 			PurchaseOrderItemCreateView.as_view(),
# 			name='purchase_order_item_create'
# 			),
#
# 		path(
# 			'order-items/<int:pk>/update/',
# 			PurchaseOrderItemUpdateView.as_view(),
# 			name='purchase_order_item_update'
# 			),
#
# 		path(
# 			'order-items/<int:pk>/delete/',
# 			PurchaseOrderItemDeleteView.as_view(),
# 			name='purchase_order_item_delete'
# 			),
#
# 		# ============================================
# 		# SHIPMENT URLS
# 		# ============================================
# 		path(
# 			'shipments/',
# 			PurchaseOrderListView.as_view(),  # Or create a dedicated shipment list view
# 			name='shipment_list'
# 			),
#
# 		path(
# 			'shipments/create/',
# 			ShipmentCreateView.as_view(),
# 			name='shipment_create'
# 			),
#
# 		path(
# 			'shipments/<int:pk>/',
# 			ShipmentDetailView.as_view(),
# 			name='shipment_detail'
# 			),
#
# 		path(
# 			'shipments/<int:pk>/update/',
# 			ShipmentUpdateView.as_view(),
# 			name='shipment_update'
# 			),
#
# 		path(
# 			'shipments/<int:pk>/delete/',
# 			ShipmentDeleteView.as_view(),
# 			name='shipment_delete'
# 			),
#
# 		path(
# 			'shipments/<int:pk>/receive/',
# 			shipment_receive_view,
# 			name='shipment_receive'
# 			),
#
# 		# ============================================
# 		# SHIPMENT ITEM URLS
# 		# ============================================
# 		path(
# 			'shipments/<int:shipment_id>/items/create/',
# 			ShipmentItemCreateView.as_view(),
# 			name='shipment_item_create'
# 			),
#
# 		path(
# 			'shipment-items/<int:pk>/update/',
# 			ShipmentItemUpdateView.as_view(),
# 			name='shipment_item_update'
# 			),
#
# 		path(
# 			'shipment-items/<int:pk>/delete/',
# 			ShipmentItemDeleteView.as_view(),
# 			name='shipment_item_delete'
# 			),
# 		]
