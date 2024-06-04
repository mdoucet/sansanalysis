import sys
from django.db import models
from django.contrib.auth.models import User

class Errors(models.Model):
    """
        Table for user comments
    """
    ## User
    user       = models.ForeignKey(User, null=True)
    
    ## Error text
    text       = models.TextField(null=True)
    
    ## Method path
    method     = models.CharField(max_length=200)
    
    ## URL
    url        = models.CharField(max_length=200, null=True)
    
    ## App version
    build      = models.IntegerField()
    
    ## True if the error was shown on an error page
    is_shown   = models.BooleanField()
    
    ## Time stamp
    created_on = models.DateTimeField('Created', auto_now_add=True)

    def get_user_id(self):
        """
            Return the ID of the user to which this profile is associated
        """
        return self.user.id
    get_user_id.short_description = 'User ID'
    
    def get_error_id(self):
        """
            Return the Error PK
        """
        return self.id
    get_error_id.short_description = "Error ID"

def store_error(user, text, method, url, build, is_shown=False):
    """
        Store an error.
        Returns the PK of the Error object.
    """
    try:
        if not isinstance(user, User):
            user=None
        err = Errors(user=user, url=str(url), text=str(text), method=str(method), build=build, is_shown=is_shown)
        err.save()
        return err.id
    except:
        err_msg = "Could not log error: url=%s; text=%s; method=%s; exc=%s" %(url, text, method, sys.exc_value)
        err = Errors(user=user, url='', text=err_msg, method='', build=build, is_shown=is_shown)
        err.save()
        return err.id
        
