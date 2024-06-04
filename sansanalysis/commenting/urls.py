
from django.conf.urls.defaults import *

urlpatterns = patterns(
    'sansanalysis.commenting.views',
    (r'^$', 'post_comment'),
)
