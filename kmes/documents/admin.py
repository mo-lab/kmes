from django.contrib import admin
from .models import Document, TagDocument

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
	list_display = ['document_number', 'title', 'doc_type', 'revision', 'status', 'project']
	list_filter = ['doc_type', 'status', 'discipline', 'project']
	search_fields = ['document_number', 'title']

@admin.register(TagDocument)
class TagDocumentAdmin(admin.ModelAdmin):
	list_display = ['equipment_tag', 'document', 'relation_type']
	list_filter = ['relation_type']
	search_fields = ['equipment_tag__tag_number', 'document__document_number']