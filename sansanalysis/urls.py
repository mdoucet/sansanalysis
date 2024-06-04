from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
     (r'^analysis/', include('sansanalysis.simpleplot.urls')),
     (r'^analysis/', include('sansanalysis.modeling.urls')),
     #(r'^analysis/', include('sansanalysis.refl_invert.urls')),
     (r'^comments/', include('sansanalysis.commenting.urls')),
     (r'^admin/', include(admin.site.urls)),

     # OpenID
     (r'^users/', include('sansanalysis.users.urls')),
     
     # Point the global home to the simpleplot home
     (r'^$', 'sansanalysis.simpleplot.views.home'),
)


# Dev settings for static files
#STATIC_DOC_ROOT = 'C:\Users\mathieu\workspace_2_6\sansanalysis\sansanalysis\styles'
STATIC_DOC_ROOT = '/Users/mathieu/Documents/workspace/sansanalysis/styles'

if settings.DEBUG:
    urlpatterns += patterns('',
     (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': STATIC_DOC_ROOT}),
)
