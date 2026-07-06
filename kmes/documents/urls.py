# # your_app/urls/documents.py
# from django.urls import path
# from . import views
#
# app_name = 'documents'
#
# urlpatterns = [
# 		# ============================================
# 		# DOCUMENT URLS
# 		# ============================================
# 		path(
# 			'',
# 			views.DocumentListView.as_view(),
# 			name='document_list'
# 			),
#
# 		path(
# 			'create/',
# 			views.DocumentCreateView.as_view(),
# 			name='document_create'
# 			),
#
# 		path(
# 			'create/project/<int:project_id>/',
# 				views.DocumentCreateView.as_view(),
# 			name='document_create_for_project'
# 			),
#
# 		path(
# 			'<int:pk>/',
# 				views.DocumentDetailView.as_view(),
# 			name='document_detail'
# 			),
#
# 		path(
# 			'<int:pk>/update/',
# 				views.DocumentUpdateView.as_view(),
# 			name='document_update'
# 			),
#
# 		path(
# 			'<int:pk>/delete/',
# 				views.DocumentDeleteView.as_view(),
# 			name='document_delete'
# 			),
# 		#
# 		path(
# 			'<int:pk>/new-revision/',
# 				views.DocumentRevisionCreateView.as_view(),
# 			name='document_revision_create'
# 			),
#
# 		path(
# 			'bulk-upload/',
# 			document_bulk_upload_view,
# 			name='document_bulk_upload'
# 			),
#
# 		# ============================================
# 		# TAG-DOCUMENT RELATIONSHIP URLS
# 		# ============================================
# 		path(
# 			'tag-links/create/',
# 			TagDocumentCreateView.as_view(),
# 			name='tag_document_create'
# 			),
#
# 		path(
# 			'tag-links/<int:pk>/delete/',
# 			TagDocumentDeleteView.as_view(),
# 			name='tag_document_delete'
# 			),
# 		]
