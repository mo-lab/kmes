# your_app/urls/construction.py
from django.urls import path
from .views import *

app_name = 'construction'

urlpatterns = [
		# ============================================
		# WORK PACKAGE URLS
		# ============================================
		path(
			'work-packages/',
			WorkPackageListView.as_view(),
			name='work_package_list'
			),
		
		path(
			'work-packages/create/',
			WorkPackageCreateView.as_view(),
			name='work_package_create'
			),
		
		path(
			'work-packages/create/project/<int:project_id>/',
			WorkPackageCreateView.as_view(),
			name='work_package_create_for_project'
			),
		
		path(
			'work-packages/create/project/<int:project_id>/area/<int:area_id>/',
			WorkPackageCreateView.as_view(),
			name='work_package_create_for_area'
			),
		
		path(
			'work-packages/<int:pk>/',
			WorkPackageDetailView.as_view(),
			name='work_package_detail'
			),
		
		path(
			'work-packages/<int:pk>/update/',
			WorkPackageUpdateView.as_view(),
			name='work_package_update'
			),
		
		path(
			'work-packages/<int:pk>/delete/',
			WorkPackageDeleteView.as_view(),
			name='work_package_delete'
			),
		
		path(
			'work-packages/<int:pk>/progress/',
			work_package_progress_update_view,
			name='work_package_progress_update'
			),
		
		# ============================================
		# WORK PACKAGE ITEM URLS
		# ============================================
		path(
			'work-packages/<int:work_package_id>/items/create/',
			WorkPackageItemCreateView.as_view(),
			name='work_package_item_create'
			),
		
		path(
			'work-package-items/<int:pk>/delete/',
			WorkPackageItemDeleteView.as_view(),
			name='work_package_item_delete'
			),
		
		# ============================================
		# DAILY PROGRESS REPORT URLS
		# ============================================
		path(
			'daily-reports/',
			DailyProgressReportListView.as_view(),
			name='daily_report_list'
			),
		
		path(
			'daily-reports/create/',
			DailyProgressReportCreateView.as_view(),
			name='daily_report_create'
			),
		
		path(
			'daily-reports/create/work-package/<int:work_package_id>/',
			DailyProgressReportCreateView.as_view(),
			name='daily_report_create_for_wp'
			),
		
		path(
			'daily-reports/<int:pk>/update/',
			DailyProgressReportUpdateView.as_view(),
			name='daily_report_update'
			),
		
		path(
			'daily-reports/<int:pk>/delete/',
			DailyProgressReportDeleteView.as_view(),
			name='daily_report_delete'
			),
		
		# ============================================
		# INSTALLED ITEM CHECK URLS
		# ============================================
		path(
			'installation-checks/create/',
			InstalledItemCheckCreateView.as_view(),
			name='installation_check_create'
			),
		
		path(
			'installation-checks/create/tag/<int:tag_id>/',
			InstalledItemCheckCreateView.as_view(),
			name='installation_check_create_for_tag'
			),
		
		path(
			'installation-checks/<int:pk>/',
			InstalledItemCheckDetailView.as_view(),
			name='installation_check_detail'
			),
		
		path(
			'installation-checks/<int:pk>/update/',
			InstalledItemCheckUpdateView.as_view(),
			name='installation_check_update'
			),
		
		path(
			'installation-checks/<int:check_id>/photos/upload/',
			InstallationCheckPhotoUploadView.as_view(),
			name='installation_check_photo_upload'
			),
		]
