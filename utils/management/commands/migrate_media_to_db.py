from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from utils.models import DatabaseFile, FreeTierFileStorage
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Migrate media files to database storage for Render free tier'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--max-size',
            type=int,
            default=5,
            help='Maximum file size in MB (default: 5MB)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it'
        )
    
    def handle(self, *args, **options):
        max_size_mb = options['max_size']
        dry_run = options['dry_run']
        
        media_root = Path('media')  # Adjust this path if needed
        
        if not media_root.exists():
            self.stdout.write(self.style.WARNING(f'Media directory {media_root} does not exist'))
            return
        
        migrated_count = 0
        skipped_count = 0
        
        self.stdout.write(self.style.SUCCESS(f'Starting migration (max size: {max_size_mb}MB)'))
        
        for file_path in media_root.rglob('*'):
            if file_path.is_file():
                try:
                    # Check file size
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    
                    if file_size_mb > max_size_mb:
                        self.stdout.write(
                            self.style.WARNING(f'Skipped {file_path.name} (too large: {file_size_mb:.1f}MB)')
                        )
                        skipped_count += 1
                        continue
                    
                    if dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(f'Would migrate: {file_path.name} ({file_size_mb:.1f}MB)')
                        )
                        migrated_count += 1
                    else:
                        # Read file and save to database
                        with open(file_path, 'rb') as f:
                            content = ContentFile(f.read(), name=file_path.name)
                            db_file = FreeTierFileStorage.save_file(content, max_size_mb=max_size_mb)
                            
                            self.stdout.write(
                                self.style.SUCCESS(f'Migrated: {file_path.name} -> Database ID: {db_file.id}')
                            )
                            migrated_count += 1
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error migrating {file_path.name}: {str(e)}')
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Dry run complete: {migrated_count} files would be migrated, {skipped_count} skipped')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Migration complete: {migrated_count} files migrated, {skipped_count} skipped')
            )
            
            if migrated_count > 0:
                self.stdout.write(
                    self.style.WARNING('Remember to backup your original media files before deleting them!')
                )