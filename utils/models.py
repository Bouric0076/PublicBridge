from django.db import models
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import base64
import os

class DatabaseFile(models.Model):
    """
    Model to store files directly in the database for Render free tier.
    This is a temporary solution until you upgrade to a paid plan with persistent storage.
    """
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_data = models.BinaryField()
    size = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.size} bytes)"
    
    def save_file(self, file):
        """Save a file to the database."""
        self.name = file.name
        self.content_type = file.content_type if hasattr(file, 'content_type') else 'application/octet-stream'
        self.file_data = file.read()
        self.size = len(self.file_data)
        self.save()
        return self
    
    def get_file_content(self):
        """Get the file content as bytes."""
        return self.file_data
    
    def get_base64_data(self):
        """Get the file data as base64 encoded string."""
        return base64.b64encode(self.file_data).decode('utf-8')
    
    def to_file_response(self):
        """Convert to a file-like object for HTTP response."""
        from django.http import HttpResponse
        response = HttpResponse(self.file_data, content_type=self.content_type)
        response['Content-Disposition'] = f'attachment; filename="{self.name}"'
        return response


class FreeTierFileStorage:
    """
    Utility class for handling file storage in Render free tier.
    Uses database storage for small files and provides fallback options.
    """
    
    @staticmethod
    def save_file(file_obj, max_size_mb=5):
        """
        Save a file to the database if it's small enough.
        max_size_mb: Maximum file size in megabytes (default 5MB for free tier)
        """
        if file_obj.size > max_size_mb * 1024 * 1024:
            raise ValueError(f"File too large. Maximum size is {max_size_mb}MB for free tier.")
        
        db_file = DatabaseFile()
        return db_file.save_file(file_obj)
    
    @staticmethod
    def get_file(file_id):
        """Retrieve a file from the database."""
        try:
            return DatabaseFile.objects.get(id=file_id)
        except DatabaseFile.DoesNotExist:
            return None
    
    @staticmethod
    def delete_file(file_id):
        """Delete a file from the database."""
        try:
            db_file = DatabaseFile.objects.get(id=file_id)
            db_file.delete()
            return True
        except DatabaseFile.DoesNotExist:
            return False
    
    @staticmethod
    def list_files():
        """List all stored files."""
        return DatabaseFile.objects.all()


# Example usage in views:
def handle_file_upload(request):
    """
    Example view for handling file uploads in free tier.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        try:
            # Save to database
            db_file = FreeTierFileStorage.save_file(uploaded_file, max_size_mb=5)
            return JsonResponse({
                'success': True,
                'file_id': db_file.id,
                'file_name': db_file.name,
                'file_size': db_file.size
            })
        except ValueError as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'No file provided'})