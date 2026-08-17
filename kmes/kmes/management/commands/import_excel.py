import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import EquipmentTag, Project

class Command(BaseCommand):
	help = 'Import equipment tags from Excel file'
	
	def add_arguments(self, parser):
		parser.add_argument('file_path', type=str, help='Path to Excel file')
		parser.add_argument('--project_id', type=int, help='Project ID')
		parser.add_argument('--dry_run', action='store_true', help='Preview without saving')
	
	@transaction.atomic
	def handle(self, *args, **options):
		file_path = options['file_path']
		project_id = options.get('project_id')
		dry_run = options.get('dry_run', False)
		
		self.stdout.write(f'Reading Excel file: {file_path}')
		
		try:
			df = pd.read_excel(file_path)
			self.stdout.write(f'Found columns: {df.columns.tolist()}')
			self.stdout.write(f'Total rows: {len(df)}')
			
			if dry_run:
				self.stdout.write('\n=== DRY RUN - Preview ===')
				self.stdout.write(str(df.head()))
				return
			
			project = None
			if project_id:
				project = Project.objects.get(pk=project_id)
				self.stdout.write(f'Using project: {project.name}')
			
			success_count = 0
			
			for index, row in df.iterrows():
				tag_number = f"{project.code if project else 'TAG'}-{index+1:04d}"
				
				equipment_tag = EquipmentTag(
						tag_number=tag_number,
						description=str(row.get('description', '')),
						project=project,
						status='ENG',
						equipment_type='OTHR',
						notes='\n'.join([
								f"Remarks: {row.get('remarks', '')}" if pd.notna(row.get('remarks', '')) else '',
								f"Drawing: {row.get('drawing_number', '')}" if pd.notna(row.get('drawing_number', '')) else ''
								]).strip()
						)
				equipment_tag.save()
				success_count += 1
			
			self.stdout.write(f'\n✅ Successfully imported: {success_count}')
		
		except Exception as e:
			self.stderr.write(f'Error: {e}')
			raise