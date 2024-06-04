from django.db import models
from django.contrib.auth.models import User

class UserComment(models.Model):
    """
        Table for user comments
    """
    ## User
    user       = models.ForeignKey(User)
    
    ## Comments
    text       = models.TextField()
    
    ## Is this a comment (true) or a suggestion (false)
    is_comment = models.BooleanField()
    
    ## Page ID
    page_id    = models.IntegerField()
    
    ## Status
    status     = models.IntegerField(null=True)
    
    ## App version
    build      = models.IntegerField()
    
    ## Time stamp
    created_on = models.DateTimeField('Created', auto_now_add=True)

    def get_user_id(self):
        """
            Return the ID of the user to which this profile is associated
        """
        return self.user.id
    get_user_id.short_description = 'ID'


class Page(models.Model):
    """
        Table for individual page IDs
    """
    url = models.CharField(max_length=200, unique=True)
    
    def get_page_id(self):
        """
            Return the PK for this page
        """
        return self.id
    get_page_id.short_description = 'Page ID'
