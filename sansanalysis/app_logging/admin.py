from sansanalysis.app_logging.models import Errors
from django.contrib import admin

class ErrorsAdmin(admin.ModelAdmin):
    list_display = ('get_error_id', 'get_user_id', 'is_shown', 'build', 'url', 'user', 'text', 'method', 'created_on')


admin.site.register(Errors, ErrorsAdmin)


