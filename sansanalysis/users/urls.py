
from django.conf.urls.defaults import *

urlpatterns = patterns(
    'sansanalysis.users.views',
    (r'^$', 'startOpenID'),
    (r'^finish/$', 'finishOpenID'),
    (r'^xrds/$', 'rpXRDS'),
    (r'^registration/$', 'registration'),
    (r'^logout/$', 'logout_view'),
)
