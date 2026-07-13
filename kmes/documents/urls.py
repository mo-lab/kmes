from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
		# ============================================
		# DOCUMENT CRUD
		# ============================================
		
		# List all documents
		# path('', views.DocumentListView.as_view(), name='document_list'),
		
		# Create new document
		path('create/', views.DocumentCreateView.as_view(), name='document-create'),
		
		# # Create document for a specific project
		# path('create/project/<int:project_id>/',
		#      views.DocumentCreateView.as_view(),
		#      name='document_create_for_project'),
		#
		# # Document detail view
		# path('<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
		#
		# # Update existing document
		# path('<int:pk>/update/', views.DocumentUpdateView.as_view(), name='document_update'),
		#
		# # Delete document
		# path('<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
		#
		# # Create new revision of a document
		# path('<int:pk>/new-revision/',
		#      views.DocumentRevisionCreateView.as_view(),
		#      name='document_revision'),
		#
		# # ============================================
		# # BULK OPERATIONS
		# # ============================================
		#
		# # Bulk upload multiple documents
		# path('bulk-upload/', views.document_bulk_upload_view, name='document_bulk_upload'),
		#
		# # Bulk upload for specific project
		# path('bulk-upload/project/<int:project_id>/',
		#      views.document_bulk_upload_view,
		#      name='document_bulk_upload_for_project'),
		#
		# # ============================================
		# # TAG-DOCUMENT RELATIONSHIPS
		# # ============================================
		#
		# # Link document to equipment tag
		# path('tag-document/create/',
		#      views.TagDocumentCreateView.as_view(),
		#      name='tag_document_create'),
		#
		# # Unlink document from equipment tag
		# path('tag-document/<int:pk>/delete/',
		#      views.TagDocumentDeleteView.as_view(),
		#      name='tag_document_delete'),
		#
		# # ============================================
		# # DOCUMENT DOWNLOAD
		# # ============================================
		#
		# # Download document file
		# path('<int:pk>/download/',
		#      views.document_download_view,
		#      name='document_download'),
		]