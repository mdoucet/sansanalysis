from sansanalysis.simpleplot.models import IqData, IqDataPoint, RecentData 
from sansanalysis.simpleplot.models import PrInversion, AnonymousSharedData, UserSharedData
from sansanalysis.simpleplot.models import AnonymousSharedPr, UserSharedPr

from django.contrib import admin

class IqDataAdmin(admin.ModelAdmin):
    list_display = ('file', 'name', 'owner', 'modified_on', 'created_on')
    list_filter = ['modified_on']
    search_fields = ['file']
    date_hierarchy = 'modified_on'

class IqDataPointAdmin(admin.ModelAdmin):
    list_display = ('get_file_name', 'x', 'y', 'dy')

class RecentDataAdmin(admin.ModelAdmin):
    list_display = ('get_file_name', 'user_id', 'get_user_name', 'visited_on')
    list_filter = ['visited_on', 'user_id']
    date_hierarchy = 'visited_on'

class PrInversionAdmin(admin.ModelAdmin):
    list_display = ('get_description', 'get_file_name', 'user_id', 'get_user_name', 'created_on')
    list_filter = ['created_on', 'user_id']
    date_hierarchy = 'created_on'

class AnonymousSharedDataAdmin(admin.ModelAdmin):
    list_display = ('get_file_name', 'shared_key')

class AnonymousSharedPrAdmin(admin.ModelAdmin):
    list_display = ('get_file_name', 'shared_key')

class UserSharedDataAdmin(admin.ModelAdmin):
    list_display = ('get_file_name', 'get_user_name')

class UserSharedPrAdmin(admin.ModelAdmin):
    list_display = ('get_file_name', 'get_user_name')


admin.site.register(IqData, IqDataAdmin)
admin.site.register(IqDataPoint, IqDataPointAdmin)
admin.site.register(RecentData, RecentDataAdmin)
admin.site.register(PrInversion, PrInversionAdmin)
admin.site.register(AnonymousSharedData, AnonymousSharedDataAdmin)
admin.site.register(UserSharedData, UserSharedDataAdmin)
admin.site.register(AnonymousSharedPr, AnonymousSharedPrAdmin)
admin.site.register(UserSharedPr, UserSharedPrAdmin)
