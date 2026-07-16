# your_app/urls/core.py
from django.urls import path

# from core.views import ProjectListView, ProjectCreateView, ProjectDetailView, ProjectUpdateView, ProjectDeleteView, AreaListView, AreaCreateView, \
# 	AreaUpdateView, AreaDeleteView, SystemListView, SystemCreateView, SystemUpdateView, SystemDeleteView, EquipmentTagListView, \
# 	EquipmentTagCreateView, EquipmentTagDetailView, EquipmentTagUpdateView, EquipmentTagDeleteView, equipment_tag_hierarchy_view, \
# 	equipment_tag_bulk_update_view, ajax_load_areas, ajax_load_systems, ajax_load_tags
from . import views

app_name = 'core'

# urlpatterns = [
# 		# ============================================
# 		# PROJECT URLS
# 		# ============================================
# 		path(
# 			'projects/',
# 			ProjectListView.as_view(),
# 			name='project_list'
# 			),
#
# 		path(
# 			'projects/create/',
# 			ProjectCreateView.as_view(),
# 			name='project_create'
# 			),
#
# 		path(
# 			'projects/<int:pk>/',
# 			ProjectDetailView.as_view(),
# 			name='project_detail'
# 			),
#
# 		path(
# 			'projects/<int:pk>/update/',
# 			ProjectUpdateView.as_view(),
# 			name='project_update'
# 			),
#
# 		path(
# 			'projects/<int:pk>/delete/',
# 			ProjectDeleteView.as_view(),
# 			name='project_delete'
# 			),
#
# 		# ============================================
# 		# AREA URLS
# 		# ============================================
# 		path(
# 			'areas/',
# 			AreaListView.as_view(),
# 			name='area_list'
# 			),
#
# 		path(
# 			'areas/create/',
# 			AreaCreateView.as_view(),
# 			name='area_create'
# 			),
#
# 		path(
# 			'areas/create/project/<int:project_id>/',
# 			AreaCreateView.as_view(),
# 			name='area_create_for_project'
# 			),
#
# 		path(
# 			'areas/<int:pk>/update/',
# 			AreaUpdateView.as_view(),
# 			name='area_update'
# 			),
#
# 		path(
# 			'areas/<int:pk>/delete/',
# 			AreaDeleteView.as_view(),
# 			name='area_delete'
# 			),
#
# 		# ============================================
# 		# SYSTEM URLS
# 		# ============================================
# 		path(
# 			'systems/',
# 			SystemListView.as_view(),
# 			name='system_list'
# 			),
#
# 		path(
# 			'systems/create/',
# 			SystemCreateView.as_view(),
# 			name='system_create'
# 			),
#
# 		path(
# 			'systems/create/project/<int:project_id>/',
# 			SystemCreateView.as_view(),
# 			name='system_create_for_project'
# 			),
#
# 		path(
# 			'systems/<int:pk>/update/',
# 			SystemUpdateView.as_view(),
# 			name='system_update'
# 			),
#
# 		path(
# 			'systems/<int:pk>/delete/',
# 			SystemDeleteView.as_view(),
# 			name='system_delete'
# 			),
#
# 		# ============================================
# 		# EQUIPMENT TAG URLS
# 		# ============================================
# 		path(
# 			'tags/',
# 			EquipmentTagListView.as_view(),
# 			name='equipment_tag_list'
# 			),
#
# 		path(
# 			'tags/create/',
# 			EquipmentTagCreateView.as_view(),
# 			name='equipment_tag_create'
# 			),
#
# 		path(
# 			'tags/create/project/<int:project_id>/',
# 			EquipmentTagCreateView.as_view(),
# 			name='equipment_tag_create_for_project'
# 			),
#
# 		path(
# 			'tags/<int:pk>/',
# 			EquipmentTagDetailView.as_view(),
# 			name='equipment_tag_detail'
# 			),
#
# 		path(
# 			'tags/<int:pk>/update/',
# 			EquipmentTagUpdateView.as_view(),
# 			name='equipment_tag_update'
# 			),
#
# 		path(
# 			'tags/<int:pk>/delete/',
# 			EquipmentTagDeleteView.as_view(),
# 			name='equipment_tag_delete'
# 			),
#
# 		path(
# 			'tags/<int:pk>/hierarchy/',
# 			equipment_tag_hierarchy_view,
# 			name='equipment_tag_hierarchy'
# 			),
#
# 		path(
# 			'tags/bulk-update/',
# 			equipment_tag_bulk_update_view,
# 			name='equipment_tag_bulk_update'
# 			),
#
# 		# ============================================
# 		# AJAX ENDPOINTS
# 		# ============================================
# 		path(
# 			'ajax/load-areas/',
# 			ajax_load_areas,
# 			name='ajax_load_areas'
# 			),
#
# 		path(
# 			'ajax/load-systems/',
# 			ajax_load_systems,
# 			name='ajax_load_systems'
# 			),
#
# 		path(
# 			'ajax/load-tags/',
# 			ajax_load_tags,
# 			name='ajax_load_tags'
# 			),
# 		]
urlpatterns = [
		path("projects/create/", views.ProjectCreateView.as_view(), name="project-create"),
		path("projects/<int:project_pk>/areas/create/", views.AreaCreateView.as_view(), name="area-create"),
		path("projects/<int:project_pk>/systems/create/", views.SystemCreateView.as_view(), name="system-create"),
		path("projects/<int:project_pk>/tags/create/", views.EquipmentTagCreateView.as_view(), name="equipmenttag-create"),
		path('projects/', views.ProjectListView.as_view(), name='project-list'),
		path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
		path('equipments/', views.EquipmentTagListView.as_view(), name='equipment-tag-list'),
		path('tags/<int:pk>/', views.EquipmentTagDetailView.as_view(), name='equipment-tag-detail'),
		path(
			'tags/<int:tag_id>/location/create/',
			views.EquipmentLocationCreateView.as_view(),
			name='equipment_location_create'
			),
		path(
			'locations/<int:pk>/',
			views.EquipmentLocationDetailView.as_view(),
			name='equipment_location_detail'
			),
		path(
			'locations/<int:location_id>/upload-image/',
			views.upload_location_image,
			name='upload_location_image'
			),
		path(
			'locations/image/<int:image_id>/delete/',
			views.delete_location_image,
			name='delete_location_image'
			),
		path(
			'locations/image/<int:image_id>/set-primary/',
			views.set_primary_image,
			name='set_primary_image'
			),
		path(
			'locations/<int:location_id>/verify/',
			views.verify_location,
			name='verify_location'
			),
		
		]
