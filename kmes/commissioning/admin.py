from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
	CommissioningSystem, TestProcedure, TestRecord,
	PunchItem, PunchItemPhoto
	)


# ============================================
# PUNCH ITEM PHOTO INLINE
# ============================================

class PunchItemPhotoInline(admin.TabularInline):
	model = PunchItemPhoto
	extra = 0
	fields = ['photo', 'photo_type', 'caption', 'preview']
	readonly_fields = ['preview']
	
	def preview(self, obj):
		if obj.photo:
			return format_html(
					'<img src="{}" style="max-height: 100px; max-width: 150px;" />',
					obj.photo.url
					)
		return "No image"
	preview.short_description = 'Preview'


# ============================================
# TEST RECORD INLINE
# ============================================

class TestRecordInline(admin.TabularInline):
	model = TestRecord
	extra = 0
	fields = [
			'test_number', 'executed_by', 'start_datetime',
			'end_datetime', 'result', 'status_badge'
			]
	readonly_fields = ['status_badge']
	show_change_link = True
	
	def status_badge(self, obj):
		colors = {
				'PASS': 'green',
				'COND': 'orange',
				'FAIL': 'red',
				'IPRO': 'blue'
				}
		color = colors.get(obj.result, 'gray')
		return format_html(
				'<span style="color: {}; font-weight: bold;">{}</span>',
				color,
				obj.get_result_display()
				)
	status_badge.short_description = 'Result'


# ============================================
# TEST PROCEDURE INLINE
# ============================================

class TestProcedureInline(admin.TabularInline):
	model = TestProcedure
	extra = 0
	fields = ['code', 'description', 'test_type', 'is_mandatory', 'status']
	readonly_fields = ['status']
	show_change_link = True
	
	def status(self, obj):
		# Get latest test record status
		latest_record = obj.test_records.order_by('-start_datetime').first()
		if latest_record:
			return latest_record.get_result_display()
		return "Not Tested"
	status.short_description = 'Latest Result'


# ============================================
# COMMISSIONING SYSTEM ADMIN
# ============================================

@admin.register(CommissioningSystem)
class CommissioningSystemAdmin(admin.ModelAdmin):
	list_display = [
			'system_code', 'system_name', 'project_name',
			'status_badge', 'progress_bar', 'planned_start',
			'planned_finish', 'actual_start', 'actual_finish',
			'lead_engineer'
			]
	list_filter = [
			'status',
			'system__project',
			]
	search_fields = [
			'system__code',
			'system__name',
			'system__project__name',
			]
	readonly_fields = [
			'created_at', 'updated_at', 'progress_percentage',
			'passed_tests', 'total_tests'
			]
	fieldsets = (
			('System Information', {
					'fields': ('system', 'lead_engineer')
					}),
			('Status', {
					'fields': ('status', 'progress_percentage', 'passed_tests', 'total_tests')
					}),
			('Schedule', {
					'fields': ('planned_start', 'planned_finish', 'actual_start', 'actual_finish')
					}),
			('Notes', {
					'fields': ('notes',)
					}),
			('Metadata', {
					'fields': ('created_at', 'updated_at'),
					'classes': ('collapse',)
					}),
			)
	inlines = [TestProcedureInline]
	
	def system_code(self, obj):
		return obj.system.code
	system_code.short_description = 'System Code'
	system_code.admin_order_field = 'system__code'
	
	def system_name(self, obj):
		return obj.system.name
	system_name.short_description = 'System Name'
	system_name.admin_order_field = 'system__name'
	
	def project_name(self, obj):
		return obj.system.project.name
	project_name.short_description = 'Project'
	project_name.admin_order_field = 'system__project__name'
	
	def status_badge(self, obj):
		colors = {
				'PREC': '#6c757d',
				'COLD': '#0dcaf0',
				'HOT': '#fd7e14',
				'RAMP': '#ffc107',
				'PERF': '#0d6efd',
				'HNDO': '#198754',
				}
		color = colors.get(obj.status, '#6c757d')
		return format_html(
				'<span style="background-color: {}; color: white; padding: 4px 8px; '
				'border-radius: 4px; font-size: 0.85em;">{}</span>',
				color,
				obj.get_status_display()
				)
	status_badge.short_description = 'Status'
	status_badge.admin_order_field = 'status'
	
	def progress_bar(self, obj):
		total = obj.test_procedures.count()
		if total == 0:
			return format_html(
					'<div style="background: #e9ecef; border-radius: 4px; width: 150px; '
					'height: 20px;"><div style="width: 0%; height: 100%; '
					'background: #0d6efd; border-radius: 4px;"></div></div>'
					)
		
		passed = TestRecord.objects.filter(
				test_procedure__commissioning_system=obj,
				result='PASS'
				).values('test_procedure').distinct().count()
		
		percentage = int((passed / total) * 100)
		color = '#198754' if percentage >= 100 else '#ffc107' if percentage >= 50 else '#0d6efd'
		
		return format_html(
				'<div style="background: #e9ecef; border-radius: 4px; width: 150px; '
				'height: 20px;"><div style="width: {}%; height: 100%; '
				'background: {}; border-radius: 4px; text-align: center; '
				'font-size: 0.75em; color: white; line-height: 20px;">{}%</div></div>',
				percentage, color, percentage
				)
	progress_bar.short_description = 'Progress'
	
	def progress_percentage(self, obj):
		total = obj.test_procedures.count()
		if total == 0:
			return "0%"
		passed = TestRecord.objects.filter(
				test_procedure__commissioning_system=obj,
				result='PASS'
				).values('test_procedure').distinct().count()
		return f"{int((passed / total) * 100)}% ({passed}/{total})"
	progress_percentage.short_description = 'Progress'
	
	def passed_tests(self, obj):
		return TestRecord.objects.filter(
				test_procedure__commissioning_system=obj,
				result='PASS'
				).values('test_procedure').distinct().count()
	passed_tests.short_description = 'Passed Tests'
	
	def total_tests(self, obj):
		return obj.test_procedures.count()
	total_tests.short_description = 'Total Tests'


# ============================================
# TEST PROCEDURE ADMIN
# ============================================

@admin.register(TestProcedure)
class TestProcedureAdmin(admin.ModelAdmin):
	list_display = [
			'code', 'description', 'commissioning_system_info',
			'test_type_badge', 'is_mandatory_badge', 'duration_hours',
			'latest_result', 'prerequisites_count'
			]
	list_filter = [
			'test_type',
			'is_mandatory',
			'commissioning_system__system__project',
			'commissioning_system__status',
			]
	search_fields = [
			'code',
			'description',
			'commissioning_system__system__code',
			'commissioning_system__system__name',
			]
	filter_horizontal = ['prerequisites', 'equipment_tags']
	readonly_fields = ['created_at', 'updated_at']
	fieldsets = (
			('Procedure Information', {
					'fields': ('commissioning_system', 'code', 'description', 'test_type')
					}),
			('Details', {
					'fields': ('duration_hours', 'is_mandatory', 'procedure_document')
					}),
			('Relationships', {
					'fields': ('prerequisites', 'equipment_tags')
					}),
			('Metadata', {
					'fields': ('created_at', 'updated_at'),
					'classes': ('collapse',)
					}),
			)
	inlines = [TestRecordInline]
	
	def commissioning_system_info(self, obj):
		return f"{obj.commissioning_system.system.code} - {obj.commissioning_system.system.name}"
	commissioning_system_info.short_description = 'Commissioning System'
	commissioning_system_info.admin_order_field = 'commissioning_system__system__code'
	
	def test_type_badge(self, obj):
		colors = {
				'PREC': '#6c757d',
				'COLD': '#0dcaf0',
				'HOT': '#fd7e14',
				'PERF': '#0d6efd',
				'FUNC': '#6610f2',
				'SAFE': '#dc3545',
				}
		color = colors.get(obj.test_type, '#6c757d')
		return format_html(
				'<span style="background-color: {}; color: white; padding: 2px 6px; '
				'border-radius: 3px; font-size: 0.8em;">{}</span>',
				color, obj.get_test_type_display()
				)
	test_type_badge.short_description = 'Type'
	test_type_badge.admin_order_field = 'test_type'
	
	def is_mandatory_badge(self, obj):
		if obj.is_mandatory:
			return format_html(
					'<span style="color: #dc3545;">&#10004; Mandatory</span>'
					)
		return format_html(
				'<span style="color: #6c757d;">Optional</span>'
				)
	is_mandatory_badge.short_description = 'Required'
	is_mandatory_badge.admin_order_field = 'is_mandatory'
	
	def latest_result(self, obj):
		latest_record = obj.test_records.order_by('-start_datetime').first()
		if latest_record:
			colors = {
					'PASS': 'green',
					'COND': 'orange',
					'FAIL': 'red',
					'IPRO': 'blue'
					}
			color = colors.get(latest_record.result, 'gray')
			return format_html(
					'<span style="color: {}; font-weight: bold;">{}</span>',
					color,
					latest_record.get_result_display()
					)
		return format_html('<span style="color: #6c757d;">Not Tested</span>')
	latest_result.short_description = 'Latest Result'
	
	def prerequisites_count(self, obj):
		count = obj.prerequisites.count()
		if count == 0:
			return "None"
		return str(count)
	prerequisites_count.short_description = 'Prerequisites'


# ============================================
# TEST RECORD ADMIN
# ============================================

@admin.register(TestRecord)
class TestRecordAdmin(admin.ModelAdmin):
	list_display = [
			'procedure_info', 'test_number', 'result_badge',
			'executed_by', 'witnessed_by', 'start_datetime',
			'end_datetime', 'duration'
			]
	list_filter = [
			'result',
			'test_procedure__commissioning_system__system__project',
			'test_procedure__test_type',
			]
	search_fields = [
			'test_procedure__code',
			'test_procedure__description',
			'executed_by__username',
			'comments',
			]
	readonly_fields = [
			'created_at', 'updated_at', 'duration',
			'signature_preview', 'witnessed_signature_preview'
			]
	fieldsets = (
			('Test Information', {
					'fields': ('test_procedure', 'test_number')
					}),
			('Results', {
					'fields': ('result', 'comments')
					}),
			('Personnel', {
					'fields': ('executed_by', 'witnessed_by')
					}),
			('Timing', {
					'fields': ('start_datetime', 'end_datetime', 'duration')
					}),
			('Signatures', {
					'fields': ('signature', 'signature_preview', 'witnessed_signature', 'witnessed_signature_preview'),
					'classes': ('collapse',)
					}),
			('Metadata', {
					'fields': ('created_at', 'updated_at'),
					'classes': ('collapse',)
					}),
			)
	
	def procedure_info(self, obj):
		url = reverse('admin:commissioning_testprocedure_change', args=[obj.test_procedure.pk])
		return format_html(
				'<a href="{}">{}</a>',
				url,
				obj.test_procedure.code
				)
	procedure_info.short_description = 'Test Procedure'
	procedure_info.admin_order_field = 'test_procedure__code'
	
	def result_badge(self, obj):
		colors = {
				'PASS': '#198754',
				'COND': '#fd7e14',
				'FAIL': '#dc3545',
				'IPRO': '#0d6efd',
				}
		color = colors.get(obj.result, '#6c757d')
		return format_html(
				'<span style="background-color: {}; color: white; padding: 4px 8px; '
				'border-radius: 4px; font-weight: bold;">{}</span>',
				color, obj.get_result_display()
				)
	result_badge.short_description = 'Result'
	result_badge.admin_order_field = 'result'
	
	def duration(self, obj):
		if obj.start_datetime and obj.end_datetime:
			delta = obj.end_datetime - obj.start_datetime
			hours = delta.total_seconds() / 3600
			return f"{hours:.1f} hours"
		return "-"
	duration.short_description = 'Duration'
	
	def signature_preview(self, obj):
		if obj.signature:
			return format_html(
					'<img src="{}" style="max-height: 100px; border: 1px solid #ddd;" />',
					obj.signature.url
					)
		return "No signature"
	signature_preview.short_description = 'Signature Preview'
	
	def witnessed_signature_preview(self, obj):
		if obj.witnessed_signature:
			return format_html(
					'<img src="{}" style="max-height: 100px; border: 1px solid #ddd;" />',
					obj.witnessed_signature.url
					)
		return "No signature"
	witnessed_signature_preview.short_description = 'Witness Signature Preview'


# ============================================
# PUNCH ITEM ADMIN
# ============================================

@admin.register(PunchItem)
class PunchItemAdmin(admin.ModelAdmin):
	list_display = [
			'punch_number', 'description_truncated', 'category_badge',
			'status_badge', 'equipment_tag_link', 'system_link',
			'raised_by', 'raised_date', 'assigned_to_info',
			'due_date', 'is_overdue'
			]
	list_filter = [
			'category',
			'status',
			'project',
			'raised_date',
			]
	search_fields = [
			'punch_number',
			'description',
			'equipment_tag__tag_number',
			'assigned_to_contractor',
			]
	readonly_fields = [
			'created_at', 'updated_at', 'raised_date',
			'resolved_date', 'verified_date'
			]
	fieldsets = (
			('Punch Item Information', {
					'fields': ('project', 'punch_number', 'description')
					}),
			('Classification', {
					'fields': ('category', 'status')
					}),
			('Related Items', {
					'fields': ('equipment_tag', 'system', 'test_record')
					}),
			('Assignment', {
					'fields': ('raised_by', 'raised_date', 'assigned_to_contractor', 'assigned_to', 'due_date')
					}),
			('Resolution', {
					'fields': ('resolved_date', 'verified_by', 'verified_date'),
					'classes': ('collapse',)
					}),
			('Metadata', {
					'fields': ('created_at', 'updated_at'),
					'classes': ('collapse',)
					}),
			)
	inlines = [PunchItemPhotoInline]
	actions = ['mark_as_resolved', 'mark_as_verified', 'export_as_csv']
	
	def description_truncated(self, obj):
		return obj.description[:80] + ('...' if len(obj.description) > 80 else '')
	description_truncated.short_description = 'Description'
	
	def category_badge(self, obj):
		colors = {
				'A': '#dc3545',
				'B': '#fd7e14',
				'C': '#6c757d',
				}
		color = colors.get(obj.category, '#6c757d')
		return format_html(
				'<span style="background-color: {}; color: white; padding: 2px 6px; '
				'border-radius: 3px; font-size: 0.8em;">{}</span>',
				color, obj.get_category_display()
				)
	category_badge.short_description = 'Category'
	category_badge.admin_order_field = 'category'
	
	def status_badge(self, obj):
		colors = {
				'OPEN': '#dc3545',
				'IPRO': '#0d6efd',
				'RESL': '#fd7e14',
				'CLSD': '#198754',
				'REJ': '#6c757d',
				}
		color = colors.get(obj.status, '#6c757d')
		return format_html(
				'<span style="background-color: {}; color: white; padding: 4px 8px; '
				'border-radius: 4px; font-size: 0.85em;">{}</span>',
				color, obj.get_status_display()
				)
	status_badge.short_description = 'Status'
	status_badge.admin_order_field = 'status'
	
	def equipment_tag_link(self, obj):
		if obj.equipment_tag:
			url = reverse('admin:core_equipmenttag_change', args=[obj.equipment_tag.pk])
			return format_html(
					'<a href="{}">{}</a>',
					url, obj.equipment_tag.tag_number
					)
		return "-"
	equipment_tag_link.short_description = 'Equipment Tag'
	
	def system_link(self, obj):
		if obj.system:
			url = reverse('admin:core_system_change', args=[obj.system.pk])
			return format_html(
					'<a href="{}">{}</a>',
					url, obj.system.code
					)
		return "-"
	system_link.short_description = 'System'
	
	def assigned_to_info(self, obj):
		if obj.assigned_to:
			return obj.assigned_to.get_full_name() or obj.assigned_to.username
		elif obj.assigned_to_contractor:
			return f"📋 {obj.assigned_to_contractor}"
		return "-"
	assigned_to_info.short_description = 'Assigned To'
	
	def is_overdue(self, obj):
		if obj.due_date and obj.status in ['OPEN', 'IPRO']:
			if timezone.now().date() > obj.due_date:
				return format_html(
						'<span style="color: #dc3545; font-weight: bold;">⚠ Overdue</span>'
						)
		return ""
	is_overdue.short_description = ''
	
	# Custom admin actions
	def mark_as_resolved(self, request, queryset):
		updated = queryset.filter(status__in=['OPEN', 'IPRO']).update(
				status='RESL',
				resolved_date=timezone.now().date()
				)
		self.message_user(request, f"{updated} punch items marked as resolved.")
	mark_as_resolved.short_description = "Mark selected as Resolved"
	
	def mark_as_verified(self, request, queryset):
		updated = queryset.filter(status='RESL').update(
				status='CLSD',
				verified_by=request.user,
				verified_date=timezone.now().date()
				)
		self.message_user(request, f"{updated} punch items verified and closed.")
	mark_as_verified.short_description = "Verify and Close selected"
	
	def export_as_csv(self, request, queryset):
		import csv
		from django.http import HttpResponse
		
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="punch_items.csv"'
		
		writer = csv.writer(response)
		writer.writerow([
				'Punch Number', 'Description', 'Category', 'Status',
				'Equipment Tag', 'System', 'Raised By', 'Raised Date',
				'Assigned To', 'Due Date', 'Resolved Date', 'Verified Date'
				])
		
		for item in queryset:
			writer.writerow([
					item.punch_number,
					item.description,
					item.get_category_display(),
					item.get_status_display(),
					item.equipment_tag.tag_number if item.equipment_tag else '',
					item.system.code if item.system else '',
					item.raised_by.get_full_name() if item.raised_by else '',
					item.raised_date,
					item.assigned_to.get_full_name() if item.assigned_to else item.assigned_to_contractor,
					item.due_date,
					item.resolved_date,
					item.verified_date,
					])
		
		return response
	export_as_csv.short_description = "Export selected as CSV"


# ============================================
# PUNCH ITEM PHOTO ADMIN
# ============================================

@admin.register(PunchItemPhoto)
class PunchItemPhotoAdmin(admin.ModelAdmin):
	list_display = [
			'punch_item_link', 'photo_type_badge', 'caption',
			'photo_preview', 'uploaded_at'
			]
	list_filter = [
			'photo_type',
			'uploaded_at',
			]
	search_fields = [
			'punch_item__punch_number',
			'caption',
			]
	readonly_fields = ['uploaded_at', 'photo_preview']
	fieldsets = (
			('Photo Information', {
					'fields': ('punch_item', 'photo_type', 'caption')
					}),
			('File', {
					'fields': ('photo', 'photo_preview')
					}),
			('Metadata', {
					'fields': ('uploaded_at',),
					'classes': ('collapse',)
					}),
			)
	
	def punch_item_link(self, obj):
		url = reverse('admin:commissioning_punchitem_change', args=[obj.punch_item.pk])
		return format_html(
				'<a href="{}">{}</a>',
				url, obj.punch_item.punch_number
				)
	punch_item_link.short_description = 'Punch Item'
	punch_item_link.admin_order_field = 'punch_item__punch_number'
	
	def photo_type_badge(self, obj):
		colors = {
				'BEFORE': '#dc3545',
				'AFTER': '#198754',
				}
		color = colors.get(obj.photo_type, '#6c757d')
		return format_html(
				'<span style="background-color: {}; color: white; padding: 2px 6px; '
				'border-radius: 3px;">{}</span>',
				color, obj.get_photo_type_display()
				)
	photo_type_badge.short_description = 'Type'
	
	def photo_preview(self, obj):
		if obj.photo:
			return format_html(
					'<img src="{}" style="max-height: 150px; max-width: 200px; '
					'border: 1px solid #ddd; border-radius: 4px;" />',
					obj.photo.url
					)
		return "No photo"
	photo_preview.short_description = 'Preview'