from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('sansanalysis.simpleplot.views',
    (r'^$', 'home'),
    (r'^sample$', 'sample_data'),
    (r'^(?P<iq_id>\d+)/delete/$', 'delete_data'),
    (r'^(?P<iq_id>\d+)/invert/$', 'invert'),
    (r'^(?P<iq_id>\d+)/invert/(?P<pr_id>\d+)/$', 'invert'),
    (r'^(?P<iq_id>\d+)/details/$', 'data_details'),
    (r'^dashboard/$', 'select_data'),
    (r'^(?P<iq_id>\d+)/pr_estimate/$', 'get_estimates'),
    (r'^(?P<iq_id>\d+)/explore_pr/$', 'explore_dmax'),
    (r'^(?P<iq_id>\d+)/share/$', 'share_data'),
    (r'^share/(?P<key>\w+)/$', 'access_shared_data'),
    (r'^share/(?P<key>\w+)/store$', 'store_data'),
    (r'^(?P<iq_id>\d+)/invert/(?P<pr_id>\d+)/share$', 'share_pr'),
    (r'^(?P<iq_id>\d+)/invert/(?P<pr_id>\d+)/delete$', 'delete_pr'),
    (r'^share/pr/(?P<key>\w+)/$', 'access_shared_pr'),
    (r'^share/pr/(?P<key>\w+)/store$', 'store_pr'),
    (r'^about$', 'about_site'),
    

)
