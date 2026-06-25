"""
URL configuration for kmes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
# urls.py
from django.urls import path
from ..core import views as core_views
from ..construction import views as construction_views
from ..commissioning import views as commissioning_views
from ..documents import views as document_views
from ..procurement import views as procurement_views
from ..resources import views as resource_views

urlpatterns = [
		path("admin/", admin.site.urls),
		
		# Core - Projects
		path('projects/', core_views.ProjectListView.as_view(), name='project_list'),
		path('projects/create/', core_views.ProjectCreateView.as_view(), name='project_create'),
		path('projects/<int:pk>/', core_views.ProjectDetailView.as_view(), name='project_detail'),
		path('projects/<int:pk>/update/', core_views.ProjectUpdateView.as_view(), name='project_update'),
		path('projects/<int:pk>/delete/', core_views.ProjectDeleteView.as_view(), name='project_delete'),
		
		# Core - Equipment Tags
		path('tags/', core_views.EquipmentTagListView.as_view(), name='equipment_tag_list'),
		path('tags/create/', core_views.EquipmentTagCreateView.as_view(), name='equipment_tag_create'),
		path('tags/<int:pk>/', core_views.EquipmentTagDetailView.as_view(), name='equipment_tag_detail'),
		path('tags/<int:pk>/update/', core_views.EquipmentTagUpdateView.as_view(), name='equipment_tag_update'),
		path('tags/<int:pk>/delete/', core_views.EquipmentTagDeleteView.as_view(), name='equipment_tag_delete'),
		path('tags/<int:pk>/hierarchy/', core_views.equipment_tag_hierarchy_view, name='equipment_tag_hierarchy'),
		path('tags/bulk-update/', core_views.equipment_tag_bulk_update_view, name='equipment_tag_bulk_update'),
		
		# # AJAX endpoints
		# path('ajax/load-areas/', views.ajax_load_areas, name='ajax_load_areas'),
		# path('ajax/load-systems/', views.ajax_load_systems, name='ajax_load_systems'),
		# path('ajax/load-tags/', views.ajax_load_tags, name='ajax_load_tags'),
		
		# Documents
		path('documents/', document_views.DocumentListView.as_view(), name='document_list'),
		path('documents/create/', document_views.DocumentCreateView.as_view(), name='document_create'),
		path('documents/<int:pk>/', document_views.DocumentDetailView.as_view(), name='document_detail'),
		path('documents/<int:pk>/update/', document_views.DocumentUpdateView.as_view(), name='document_update'),
		path('documents/<int:pk>/delete/', document_views.DocumentDeleteView.as_view(), name='document_delete'),
		path('documents/<int:pk>/new-revision/', document_views.DocumentRevisionCreateView.as_view(), name='document_revision'),
		path('documents/bulk-upload/', document_views.document_bulk_upload_view, name='document_bulk_upload'),
		
		# Procurement - Purchase Orders
		path('pos/', procurement_views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
		path('pos/create/', procurement_views.PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
		path('pos/<int:pk>/', procurement_views.PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
		path('pos/<int:pk>/update/', procurement_views.PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),
		path('pos/<int:pk>/delete/', procurement_views.PurchaseOrderDeleteView.as_view(), name='purchase_order_delete'),
		
		# Construction - Work Packages
		path('work-packages/', construction_views.WorkPackageListView.as_view(), name='work_package_list'),
		path('work-packages/create/', construction_views.WorkPackageCreateView.as_view(), name='work_package_create'),
		path('work-packages/<int:pk>/', construction_views.WorkPackageDetailView.as_view(), name='work_package_detail'),
		path('work-packages/<int:pk>/update/', construction_views.WorkPackageUpdateView.as_view(), name='work_package_update'),
		path('work-packages/<int:pk>/delete/', construction_views.WorkPackageDeleteView.as_view(), name='work_package_delete'),
		path('work-packages/<int:pk>/progress/', construction_views.work_package_progress_update_view, name='work_package_progress_update'),
		
		# Commissioning - Punch Items
		path('punch-items/', commissioning_views.PunchItemListView.as_view(), name='punch_item_list'),
		path('punch-items/create/', commissioning_views.PunchItemCreateView.as_view(), name='punch_item_create'),
		path('punch-items/<int:pk>/', commissioning_views.PunchItemDetailView.as_view(), name='punch_item_detail'),
		path('punch-items/<int:pk>/update/', commissioning_views.PunchItemUpdateView.as_view(), name='punch_item_update'),
		path('punch-items/<int:pk>/resolve/', commissioning_views.punch_item_resolve_view, name='punch_item_resolve'),
		path('punch-items/<int:pk>/verify/', commissioning_views.punch_item_verify_view, name='punch_item_verify'),
		
		# Resources - Timesheets
		path('timesheets/', resource_views.TimesheetListView.as_view(), name='timesheet_list'),
		path('timesheets/create/', resource_views.TimesheetCreateView.as_view(), name='timesheet_create'),
		path('timesheets/<int:pk>/update/', resource_views.TimesheetUpdateView.as_view(), name='timesheet_update'),
		path('timesheets/<int:pk>/delete/', resource_views.TimesheetDeleteView.as_view(), name='timesheet_delete'),
		path('timesheets/bulk-create/', resource_views.timesheet_bulk_create_view, name='timesheet_bulk_create'),
		]
