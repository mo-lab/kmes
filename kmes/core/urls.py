# your_app/urls/core.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
		path("projects/create/", views.ProjectCreateView.as_view(), name="project-create"),
		path("projects/<int:project_pk>/areas/create/", views.AreaCreateView.as_view(), name="area-create"),
		path("projects/<int:project_pk>/systems/create/", views.SystemCreateView.as_view(), name="system-create"),
		path("tags/create/en/", views.EquipmentTagCreateView.as_view(), name="equipmenttag-create"),
		path('tags/create/', views.EquipmentTagCreateView.as_view(), name='equipment_tag_create'),
		
		path('projects/', views.ProjectListView.as_view(), name='project-list'),
		path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
		path('projects/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
		path('equipments/', views.EquipmentTagListView.as_view(), name='equipment-tag-list'),
		path('tags/<int:pk>/', views.EquipmentTagDetailView.as_view(), name='equipment-tag-detail'),
		path('tags2/<int:pk>/', views.EquipmentTagDetailView.as_view(), name='equipment_tag_detail'),
		path('work-packages/timeline/', views.WorkPackageTimelineView.as_view(), name='work_package_timeline'),
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
		path('locations/<int:pk>/', views.EquipmentLocationDetailView.as_view(), name='equipment_location_detail'),
		path('locations/<int:pk>/upload-image/', views.upload_location_image, name='upload_location_image'),
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
		path(
				'manuals/crusher',
				views.crusher_ga,
				name='crusher_ga'
				),
		path(
				'manuals/dust_bonnet',
				views.dust_bonnet,
				name='dust_bonnet'
				),
		path('areas/', views.AreaListView.as_view(), name='area_list'),
		path('areas/<int:pk>/', views.AreaDetailView.as_view(), name='area_detail'),
		path('areas/create/', views.AreaCreateView.as_view(), name='area_create'),
		path('areas/<int:pk>/update/', views.AreaUpdateView.as_view(), name='area_update'),
		
		path('systems/', views.SystemListView.as_view(), name='system_list'),
		path('systems/<int:pk>/', views.SystemDetailView.as_view(), name='system_detail'),
		path('systems/create/', views.SystemCreateView.as_view(), name='system_create'),
		path('systems/update/<int:pk>', views.SystemUpdateView.as_view(), name='system_update'),
		path(
			'tags/<int:pk>/qr-code/download/',
			views.download_qr_code,
			name='download_qr_code'
			),
		path(
			'drawings/<int:pk>/',
			views.DrawingDetailView.as_view(),
			name='drawing_detail'
			),
		path(
			'tags/<int:pk>/qr-code/regenerate/',
			views.regenerate_qr_code,
			name='regenerate_qr_code'
			),
		path('tags/qr-codes/print/', views.print_qr_codes, name='print_qr_codes'),
		path(
			'tags/export-template/',
			views.export_equipment_tags_template,
			name='export_equipment_tags_template'
			),
		
		path('packing-lists/create/', views.PackingListCreateView.as_view(), name='packing_list_create'),
		path('packing-list/upload/', views.upload_packing_list, name='upload_packing_list'),
		]
