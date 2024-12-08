from django.contrib import admin

from django.contrib import admin
from .models import GovernmentAdmin, Profile, Follow


# Admin panel for managing GovernmentAdmin (ministries or departments)
class GovernmentAdminAdmin(admin.ModelAdmin):
    list_display = ('user', 'department_name', 'is_active')  # Display relevant fields
    list_filter = ('is_active',)  # Filter by active/inactive status
    search_fields = ('user__username', 'department_name')  # Search by user or department name
    ordering = ('department_name',)  # Order by department name

    # Custom action to activate/deactivate government admins
    actions = ['activate_departments', 'deactivate_departments']

    def activate_departments(self, request, queryset):
        queryset.update(is_active=True)
    activate_departments.short_description = "Activate selected departments"

    def deactivate_departments(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_departments.short_description = "Deactivate selected departments"


# Admin panel for Profile (to track citizen profiles and their engagement)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'get_following_count', 'get_follower_count')  # Key info for admin_dashboard
    search_fields = ('user__username', 'bio')  # Enable profile searching

    # Additional methods to display engagement metrics
    def get_following_count(self, obj):
        return obj.following.count()
    get_following_count.short_description = 'Following Count'

    def get_follower_count(self, obj):
        return obj.followers.count()
    get_follower_count.short_description = 'Follower Count'


# Admin panel for Follow (tracking relationships between users)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followed')  # Show follow relationships
    search_fields = ('follower__user__username', 'followed__user__username')  # Search by follower/followed


# Register the models to the admin_dashboard site
admin.site.register(GovernmentAdmin, GovernmentAdminAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Follow, FollowAdmin)
