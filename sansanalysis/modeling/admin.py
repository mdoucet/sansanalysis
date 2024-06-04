from sansanalysis.modeling.models import FitProblem, TheoryModel, ModelParameter, ModelParameterName
from django.contrib import admin

class FitProblemAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'get_model_name', 'get_data_name', 'q_min', 'q_max', 'created_on')

class TheoryModelAdmin(admin.ModelAdmin):
    list_display = ('model_id', 'get_model_name', 'created_on')

class ModelParameterAdmin(admin.ModelAdmin):
    list_display = ('get_model_id', 'get_name', 'value', 'error', 'is_fixed')

class ModelParameterNameAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(FitProblem, FitProblemAdmin)
admin.site.register(TheoryModel, TheoryModelAdmin)
admin.site.register(ModelParameter, ModelParameterAdmin)
admin.site.register(ModelParameterName, ModelParameterNameAdmin)
