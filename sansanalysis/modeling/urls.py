
from django.conf.urls.defaults import *

urlpatterns = patterns(
    'sansanalysis.modeling.views',
    #(r'^fit$', 'fit'),
    #(r'^about$', 'about_site'),
    (r'^(?P<iq_id>\d+)/fit/$', 'fit'), 
    (r'^(?P<iq_id>\d+)/fit/(?P<fit_id>\d+)/$', 'fit'),
    (r'^(?P<iq_id>\d+)/fit/(?P<fit_id>\d+)/share$', 'share_fit'),
    (r'^(?P<iq_id>\d+)/fit/(?P<fit_id>\d+)/delete$', 'delete_fit'),
    (r'^share/fit/(?P<key>\w+)/$', 'access_shared_fit'),
    (r'^share/fit/(?P<key>\w+)/store$', 'store_fit'),
    (r'^(?P<iq_id>\d+)/smearing/$', 'get_smearing_table'), 
    (r'^model/(?P<model_id>\d+)/parameters$', 'get_model_parameters'),
    (r'^smearing/(?P<model_id>\d+)/parameters/$', 'get_smearing_parameters'),
    (r'^model/(?P<model_id>\d+)/table$', 'get_model_table'),
    (r'^(?P<iq_id>\d+)/model/(?P<model_id>\d+)/$', 'get_model_update'),
    (r'^model/dialog$', 'get_fit_model_dialog'),

)
