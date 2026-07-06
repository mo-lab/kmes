# # your_app/urls/commissioning.py
# from django.urls import path
# from views import *
#
# app_name = 'commissioning'
#
# urlpatterns = [
# 		# ============================================
# 		# COMMISSIONING SYSTEM URLS
# 		# ============================================
# 		path(
# 			'systems/',
# 			CommissioningSystemListView.as_view(),
# 			name='commissioning_system_list'
# 			),
#
# 		path(
# 			'systems/create/',
# 			CommissioningSystemCreateView.as_view(),
# 			name='commissioning_system_create'
# 			),
#
# 		path(
# 			'systems/<int:pk>/',
# 			CommissioningSystemDetailView.as_view(),
# 			name='commissioning_system_detail'
# 			),
#
# 		path(
# 			'systems/<int:pk>/update/',
# 			CommissioningSystemUpdateView.as_view(),
# 			name='commissioning_system_update'
# 			),
#
# 		# ============================================
# 		# TEST PROCEDURE URLS
# 		# ============================================
# 		path(
# 			'systems/<int:commissioning_system_id>/procedures/create/',
# 			TestProcedureCreateView.as_view(),
# 			name='test_procedure_create'
# 			),
#
# 		path(
# 			'procedures/<int:pk>/update/',
# 			TestProcedureUpdateView.as_view(),
# 			name='test_procedure_update'
# 			),
#
# 		path(
# 			'procedures/<int:pk>/delete/',
# 			TestProcedureDeleteView.as_view(),
# 			name='test_procedure_delete'
# 			),
#
# 		# ============================================
# 		# TEST RECORD URLS
# 		# ============================================
# 		path(
# 			'procedures/<int:procedure_id>/records/create/',
# 			TestRecordCreateView.as_view(),
# 			name='test_record_create'
# 			),
#
# 		path(
# 			'records/<int:pk>/',
# 			TestRecordDetailView.as_view(),
# 			name='test_record_detail'
# 			),
#
# 		path(
# 			'records/<int:pk>/update/',
# 			TestRecordUpdateView.as_view(),
# 			name='test_record_update'
# 			),
#
# 		# ============================================
# 		# PUNCH ITEM URLS
# 		# ============================================
# 		path(
# 			'punch-items/',
# 			PunchItemListView.as_view(),
# 			name='punch_item_list'
# 			),
#
# 		path(
# 			'punch-items/create/',
# 			PunchItemCreateView.as_view(),
# 			name='punch_item_create'
# 			),
#
# 		path(
# 			'punch-items/create/project/<int:project_id>/',
# 			PunchItemCreateView.as_view(),
# 			name='punch_item_create_for_project'
# 			),
#
# 		path(
# 			'punch-items/<int:pk>/',
# 			PunchItemDetailView.as_view(),
# 			name='punch_item_detail'
# 			),
#
# 		path(
# 			'punch-items/<int:pk>/update/',
# 			PunchItemUpdateView.as_view(),
# 			name='punch_item_update'
# 			),
#
# 		path(
# 			'punch-items/<int:pk>/resolve/',
# 			punch_item_resolve_view,
# 			name='punch_item_resolve'
# 			),
#
# 		path(
# 			'punch-items/<int:pk>/verify/',
# 			punch_item_verify_view,
# 			name='punch_item_verify'
# 			),
#
# 		path(
# 			'punch-items/<int:punch_id>/photos/upload/',
# 			PunchItemPhotoUploadView.as_view(),
# 			name='punch_item_photo_upload'
# 			),
# 		]
