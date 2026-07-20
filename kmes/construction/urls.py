# your_app/urls/construction.py
from django.urls import path
from .views import WorkPackageCreateView, WorkPackageListView, DailyProgressReportCreateView, WorkPackageDetailView, WorkPackageItemCreateView, \
	work_package_item_bulk_add_view, work_package_item_toggle_complete_view, ajax_search_available_tags

app_name = 'construction'

urlpatterns = [
		# ============================================
		# WORK PACKAGE URLS
		# ============================================
		
		path('work-packages/', WorkPackageListView.as_view(), name='work_package_list'),
		path('work-packages/<int:pk>/', WorkPackageDetailView.as_view(), name='work_package_detail'),
		path('work-packages/create/', WorkPackageCreateView.as_view(), name='work_package_create'),
		path('daily-proccess/create/', DailyProgressReportCreateView.as_view(), name='daily_report_create'),
		path(
				'work-packages/<int:work_package_id>/items/add/',
				WorkPackageItemCreateView.as_view(),
				name='work_package_item_create'
				),
		path(
				'work-packages/<int:work_package_id>/items/bulk-add/',
				work_package_item_bulk_add_view,
				name='work_package_item_bulk_add'
				),
		path(
				'work-packages/items/<int:pk>/toggle-complete/',
				work_package_item_toggle_complete_view,
				name='work_package_item_toggle_complete'
				),
		path(
				'work-packages/<int:work_package_id>/items/bulk-add/',
				work_package_item_bulk_add_view,
				name='work_package_item_bulk_add'
				),
		# AJAX
		path(
			'work-packages/<int:work_package_id>/ajax/search-tags/',
			ajax_search_available_tags,
			name='ajax_search_available_tags'
			),
		]
