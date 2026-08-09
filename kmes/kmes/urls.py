# your_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from ..documents import urls as documents_urls
# from ..procurement import urls as procurement_urls
# from ..core import urls as core_urls
# from ..resources import urls as resources_urls
# from ..construction import urls as construction_urls
# from ..commissioning import urls as commissioning_urls
from core import views
urlpatterns = [
		path('admin/', admin.site.urls,name='admin'),
		
		# # Clean string-based includes with namespaces
		 path('core/', include('core.urls', namespace='core')),
		 path('docs/', include('documents.urls', namespace='documents')),
		 path('construction/', include('construction.urls', namespace='construction')),
		 path('resources/', include('resources.urls', namespace='resources')),
		path('', views.DashboardView.as_view(), name='dashboard'),
		# path('documents/', include('documents.urls', namespace='documents')),
		# path('procurement/', include('procurement.urls', namespace='procurement')),
		# path('construction/', include('construction.urls', namespace='construction')),
		# path('commissioning/', include('commissioning.urls', namespace='commissioning')),
		# path('resources/', include('resources.urls', namespace='resources')),
		
		# You can also include a main app URL module that combines all
		# path('', include('your_app.urls')),  # Optional: root-level urls
		]

# Serve media files in development
if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
	