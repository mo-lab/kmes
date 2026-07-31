# your_app/urls/construction.py
from django.urls import path
from .views import (WorkPackageCreateView, WorkPackageListView, DailyProgressReportCreateView, WorkPackageDetailView, WorkPackageItemCreateView, \
                    work_package_item_bulk_add_view, work_package_item_toggle_complete_view, ajax_search_available_tags, DailyProgressReportListView,
                    daily_report_approve_view, daily_report_approval_status_view, daily_report_unapprove_view, daily_report_bulk_approve_view,
                    DailyProgressReportListView2, DailyProccessReportEmployeeCreateView)

app_name = 'construction'

urlpatterns = [
		# ============================================
		# WORK PACKAGE URLS
		# ============================================
		
		path('work-packages/', WorkPackageListView.as_view(), name='work_package_list'),
		path('work-packages/<int:pk>/', WorkPackageDetailView.as_view(), name='work_package_detail'),
		path('work-packages/create/', WorkPackageCreateView.as_view(), name='work_package_create'),
		path('daily-proccess/create/', DailyProgressReportCreateView.as_view(), name='daily_report_create'),
		path('daily-proccess/', DailyProgressReportListView.as_view(), name='daily_report_list'),
		path('daily-proccess2/', DailyProgressReportListView2.as_view(), name='daily_report_list2'),
		# Daily Report Approval
		path('daily-reports/<int:pk>/approve/',
		     daily_report_approve_view,
		     name='daily_report_approve'),
		path('daily-reports/<int:pk>/unapprove/',
		     daily_report_unapprove_view,
		     name='daily_report_unapprove'),
		path('daily-reports/bulk-approve/',
		     daily_report_bulk_approve_view,
		     name='daily_report_bulk_approve'),
		path('daily-reports/<int:pk>/approval-status/',
		      daily_report_approval_status_view,
		     name='daily_report_approval_status'),
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
		path('daily-process-employee/add/', DailyProccessReportEmployeeCreateView.as_view(), name='daily_process_employee_create'),
		]
