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
		path('tags/create/project/<int:project_id>/', views.EquipmentTagCreateView.as_view(), name='equipment_tag_create_for_project'),
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
		path('areas/', views.AreaListView.as_view(), name='area_list'),
		path('areas/<int:pk>/', views.AreaDetailView.as_view(), name='area_detail'),
		path('areas/create/', views.AreaCreateView.as_view(), name='area_create'),
		path('systems/', views.SystemListView.as_view(), name='system_list'),
		path('systems/<int:pk>/', views.SystemDetailView.as_view(), name='system_detail'),
		path('systems/create/', views.SystemCreateView.as_view(), name='system_create'),

		]
