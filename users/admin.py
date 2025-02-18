from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User, GovernmentAdmin, Profile, Follow


# Custom User Form to handle additional fields
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'engagement_score')


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'engagement_score')


# Custom UserAdmin to use the custom forms
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('username', 'first_name', 'last_name', 'email', 'role', 'engagement_score', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role', 'engagement_score')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role', 'engagement_score')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


# Register User with custom UserAdmin
admin.site.register(User, CustomUserAdmin)


# GovernmentAdmin ModelAdmin customization
class GovernmentAdminAdmin(admin.ModelAdmin):
    list_display = ('user','is_active')
    list_filter = ('is_active',)
    search_fields = ('user__username',)
    ordering = ('user__username',)


# Register GovernmentAdmin model
admin.site.register(GovernmentAdmin, GovernmentAdminAdmin)


# Profile ModelAdmin customization
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'profile_picture')
    search_fields = ('user__username', 'bio')
    ordering = ('user__username',)


# Register Profile model
admin.site.register(Profile, ProfileAdmin)


# Follow ModelAdmin customization
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followed')
    search_fields = ('follower__user__username', 'followed__user__username')
    ordering = ('follower__user__username',)


# Register Follow model
admin.site.register(Follow, FollowAdmin)


