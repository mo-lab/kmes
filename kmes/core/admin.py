from django.contrib import admin
from .models import Project, Area, System, EquipmentTag, EquipmentLocation, EquipmentLocationImage, ProfileSettings, Drawing, DrawingHotSpot, \
	PackingList, PackingListItem, EquipmentGrid


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = ['name', 'code', 'location', 'status', 'start_date', 'target_completion_date']
	list_filter = ['status']
	search_fields = ['name', 'code', 'location']

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'project']
	list_filter = ['project']
	search_fields = ['code', 'name']

@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
	list_display = ['code', 'name', 'project']
	list_filter = ['project']
	search_fields = ['code', 'name']

@admin.register(EquipmentTag)
class EquipmentTagAdmin(admin.ModelAdmin):
	list_display = ['tag_number', 'description', 'equipment_type', 'status', 'project', 'area']
	list_filter = ['equipment_type', 'status', 'discipline', 'project']
	search_fields = ['tag_number', 'description']
@admin.register(EquipmentLocation)
class EquipmentTagAdmin(admin.ModelAdmin):
	list_display = ['latitude', 'longitude', 'elevation', 'accuracy', 'is_verified', 'area']
	list_filter = ['is_verified', 'recorded_by', 'equipment_tag', 'location_type']
	search_fields = ['longitude', 'latitude']
@admin.register(EquipmentLocationImage)
class EquipmentTagAdmin(admin.ModelAdmin):
	list_display = ['title', 'image_type', 'taken_date', 'is_primary', 'uploaded_by']
	list_filter = ['uploaded_by', 'image_type', 'is_primary']
	search_fields = ['title', 'description']
@admin.register(ProfileSettings)
class ProfileSettingsAdmin(admin.ModelAdmin):
	list_display = (['language'])

@admin.register(Drawing)
class DrawingAdmin(admin.ModelAdmin):
	list_display = ['name','url']
@admin.register(DrawingHotSpot)
class DrawingHotSpotsAdmin(admin.ModelAdmin):
	list_display = ['top','left','equipment_tag_ID','drawing__name','drawing__url']
	list_filter = (['drawing__name'])
	
@admin.register(PackingList)
class PackingListAdmin(admin.ModelAdmin):
	list_display = ['packing_list_num']
@admin.register(PackingListItem)
class PackingListAdmin(admin.ModelAdmin):
	list_display = ['id','material_description','total_weight_kg']

@admin.register(EquipmentGrid)
class PackingListAdmin(admin.ModelAdmin):
	list_display = ['equipment_tag','grid_x','grid_y','grid_z']
