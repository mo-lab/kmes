from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


def notifications_processor(request):
	"""Add notifications to the template context."""
	context = {
			'notifications': [],
			'notifications_count': 0,
			}
	
	if request.user.is_authenticated:
		# You can add your notification logic here
		# Example: Get unread shared documents, pending approvals, etc.
		try:
			from documents.models import DocumentShare
			unread_shares = DocumentShare.objects.filter(
					shared_with=request.user,
					is_accessed=False
					).count()
			
			if unread_shares > 0:
				context['notifications'].append({
						'icon': 'share',
						'color': 'info',
						'message': f'{unread_shares} document(s) shared with you',
						'url': '/documents/shared-with-me/',
						'created_at': timezone.now()
						})
		except:
			pass
		
		try:
			from resources.models import Timesheet
			pending_timesheets = Timesheet.objects.filter(
					is_approved=False
					).count()
			
			if pending_timesheets > 0 and request.user.is_staff:
				context['notifications'].append({
						'icon': 'clock',
						'color': 'warning',
						'message': f'{pending_timesheets} timesheet(s) pending approval',
						'url': '/resources/timesheets/?is_approved=false',
						'created_at': timezone.now()
						})
		except:
			pass
		
		try:
			from commissioning.models import PunchItem
			open_punches = PunchItem.objects.filter(
					status__in=['OPEN', 'IPRO']
					).count()
			
			if open_punches > 0:
				context['notifications'].append({
						'icon': 'flag',
						'color': 'danger',
						'message': f'{open_punches} open punch item(s)',
						'url': '/commissioning/punch-items/',
						'created_at': timezone.now()
						})
		except:
			pass
		
		context['notifications_count'] = len(context['notifications'])
	
	return context