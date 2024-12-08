from django.contrib import admin
from .models import Report, AnonymousReport, Comment
from django.contrib.auth import get_user_model
User = get_user_model()

class CommentInline(admin.TabularInline):
    model = Comment  # Replace with your actual model
    extra = 0  # Controls how many empty forms to display

class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'category', 'priority', 'created_at', 'updated_at')
    list_filter = ('status', 'category', 'priority', 'created_at')  # Added 'priority' for filtering
    search_fields = ('title', 'description', 'user__username')  # Fixed case: 'user' instead of 'User'
    actions = ['assign_to_department', 'mark_as_resolved', 'set_priority_high', 'export_to_csv']
    inlines = [CommentInline]
    ordering = ('-created_at',)  # Default ordering by newest first

    # Customizable display of 'user' field for anonymous reports
    def user(self, obj):
        return obj.user.username if obj.user else "Anonymous"
    user.short_description = "Reported By"

    # Action to assign reports to a department (government admin_dashboard)
    def assign_to_department(self, request, queryset):
        for report in queryset:
            report.status = 'under_review'  # Set the status to 'under_review'
            report.save()
        self.message_user(request, f"{queryset.count()} reports have been assigned to departments.")
    assign_to_department.short_description = "Assign selected reports to a department"

    # Action to mark selected reports as resolved
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')  # Bulk update status
        self.message_user(request, f"{queryset.count()} reports marked as resolved.")
    mark_as_resolved.short_description = "Mark selected reports as resolved"

    # Action to set the priority of reports to 'High'
    def set_priority_high(self, request, queryset):
        queryset.update(priority='high')  # Assuming a 'priority' field exists
        self.message_user(request, f"{queryset.count()} reports have been set to High priority.")
    set_priority_high.short_description = "Set priority to High"

    # Action to export selected reports to a CSV file
    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reports.csv"'

        writer = csv.writer(response)
        # Write headers
        writer.writerow(['Title', 'User', 'Status', 'Category', 'Priority', 'Created At', 'Updated At'])

        # Write report data
        for report in queryset:
            writer.writerow([
                report.title,
                report.user.username if report.user else "Anonymous",
                report.status,
                report.category,
                getattr(report, 'priority', 'N/A'),
                report.created_at,
                report.updated_at,
            ])

        self.message_user(request, f"{queryset.count()} reports have been exported to CSV.")
        return response
    export_to_csv.short_description = "Export selected reports to CSV"

# Register the admin_dashboard models
admin.site.register(Report, ReportAdmin)
admin.site.register(AnonymousReport)
