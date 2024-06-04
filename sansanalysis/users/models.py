from django.db import models
from django.contrib.auth.models import User

# import code for encoding urls and generating md5 hashes
import urllib, hashlib

GRAVATAR_TYPE = 'identicon'

class UserProfile(models.Model):
    """
        
    """
    ## Associated data
    user       = models.ForeignKey(User, unique=True)
    
    ## Registered flag to let us track whether a user filled out the registration form 
    registered = models.BooleanField()
    
    ## OpenID
    openid   = models.CharField(max_length=200, null=True)
    
    ## Gravatar URL
    gravatar   = models.URLField(null=True)
    
    ## Last modified
    modified_on = models.DateTimeField('Modified', auto_now=True)

    def __unicode__(self):
        repr  = "Username: %s\n" % self.user.username
        repr += "OpenID:   %s\n" % self.openid
        return repr

    def get_user_id(self):
        """
            Return the ID of the user to which this profile is associated
        """
        return self.user.id
    get_user_id.short_description = 'ID'

    def set_gravatar(self, email):
        self.gravatar = "http://www.gravatar.com/avatar/%s?d=%s" % (hashlib.md5(email).hexdigest(),GRAVATAR_TYPE)
        
        