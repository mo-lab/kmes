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
		path('', views.DocumentListView.as_view(), name='document_list'),
		path(
				'tag-document/create/',
				views.TagDocumentCreateView.as_view(),
				name='tag_document_create'
				),
		path(
				'tag-document/<int:pk>/delete/',
				views.TagDocumentDeleteView.as_view(),
				name='tag-document-delete'
				),
		path(
				'tag-document/bulk-link/',
				views.tag_document_bulk_link_view,
				name='tag_document_bulk_link'
				),
		path(
				'tag-document/list/',
				views.tag_document_list_view,
				name='tag_document_list'
				),
		# # Document detail view
		path('<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
		path(
				'share/<int:pk>/',
				views.document_share_view,
				name='document_share'
				),
		
		path(
				'share/<int:pk>/delete/',
				views.document_share_delete_view,
				name='document_share_delete'
				),
		
		# Resend share notification
		path(
				'share/<int:pk>/resend/',
				views.document_share_resend_view,
				name='document_share_resend'
				),
		
		path(
				'shared-by-me/',
				views.shared_by_me_view,
				name='shared_by_me'
				),
		
		# Bulk share documents
		path(
				'bulk-share/',
				views.document_bulk_share_view,
				name='document_bulk_share'
				),
		path(
				'search-users/',
				views.ajax_search_users,
				name='ajax_search_users'
				),
		path(
			'<int:pk>/download/',
			views.document_download_view,
			name='document_download'
			),
		
		# Preview document (inline)
		path(
			'<int:pk>/preview/',
			views.document_preview_view,
			name='document_preview'
			),
		
		# Download specific revision
		path(
			'<int:pk>/revision/<int:revision_pk>/download/',
			views.document_version_download_view,
			name='document_revision_download'
			),
		
		# Download multiple documents as ZIP
		path(
			'download-multiple/',
			views.document_download_multiple_view,
			name='document_download_multiple'
			),
		# Shared with me
		path('shared-with-me/', views.shared_with_me_view, name='shared_with_me'),
		path('share/<int:pk>/mark-seen/', views.mark_document_as_seen, name='mark_document_as_seen'),
		path('share/<int:pk>/mark-unread/', views.mark_document_as_unread, name='mark_document_as_unread'),
		path('share/mark-all-seen/', views.mark_all_as_seen, name='mark_all_as_seen'),
		]
