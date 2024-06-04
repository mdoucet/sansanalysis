from sansanalysis.users.models import UserProfile
from django.contrib import admin

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('get_user_id', 'user', 'openid', 'gravatar', 'registered', 'modified_on')

admin.site.register(UserProfile, UserProfileAdmin)

