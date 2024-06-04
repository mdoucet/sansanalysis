from sansanalysis.commenting.models import UserComment, Page
from django.contrib import admin

class UserCommentAdmin(admin.ModelAdmin):
    list_display = ('get_user_id', 'build', 'user', 'text', 'is_comment', 'page_id', 'status', 'created_on')

class PageAdmin(admin.ModelAdmin):
    list_display = ('get_page_id', 'url')

admin.site.register(UserComment, UserCommentAdmin)
admin.site.register(Page, PageAdmin)


