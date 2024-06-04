from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User

import os

class OverwriteStorage(FileSystemStorage):
    
    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
    
class IqData(models.Model):
    """

    """
    ## Data file
    #TODO: turn on overwrite once the view can search for existing data
    #storage = OverwriteStorage()
    storage = FileSystemStorage()
    file = models.FileField(upload_to='iq_data', storage=storage)
    ## Original name
    name = models.CharField(max_length=100)
    ## Owner
    owner = models.IntegerField()
    ## Create on
    created_on = models.DateTimeField('Created', auto_now_add=True)
    ## Last modified
    modified_on = models.DateTimeField('Modified', auto_now=True)

    def get_user_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        try:
            return User.objects.get(pk=self.owner).username
        except:
            # An exception can be raised when the owner of a data set "deletes" his
            # association to that data but a link still exists for another user.
            # The data set will then appear as owned by "System" to the user with the link.
            return "System"
    get_user_name.short_description = 'User name'

    
#class IqDataInfo(models.Model):
#    # Q label
#    q_label  = models.CharField(max_length=20)
#    q_unit   = models.CharField(max_length=20)
#    iq_label = models.CharField(max_length=20)
#    iq_unit  = models.CharField(max_length=20)
    
class IqDataPoint(models.Model):
    """
        Loaded data points
    """    
    ## Associated data set
    iq_data = models.ForeignKey(IqData)
    # Q value
    x   = models.FloatField()
    # I(Q) value
    y   = models.FloatField()
    # Error on Q
    dx  = models.FloatField(null=True)
    dy  = models.FloatField(null=True)
    ## Slit smearing length
    dxl = models.FloatField(null=True)
    ## Slit smearing width
    dxw = models.FloatField(null=True)
    
    def get_file_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.iq_data.name
    get_file_name.short_description = 'File name'

class RecentData(models.Model):
    """
        Recent IqData accessed by the user
    """
    ## Associated data
    iq_data = models.ForeignKey(IqData)
    ## Date the data was visited
    visited_on = models.DateTimeField('Visited', auto_now=True)
    ## User ID
    user_id = models.IntegerField()
    
    def get_file_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.iq_data.name
    get_file_name.short_description = 'File name'

    def get_user_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return User.objects.filter(pk=self.user_id)[0].username
    get_user_name.short_description = 'User name'


class PrInversion(models.Model):
    """
        
    """
    ## Associated data
    iq_data = models.ForeignKey(IqData)
    
    ## User ID
    user_id = models.IntegerField()
    
    ## If True, the background level will be a floating parameter in the fit
    has_bck     = models.BooleanField()
    
    ## Slit height
    slit_height = models.FloatField(null=True)
    ## Slit width
    slit_width  = models.FloatField(null=True)

    ## Number of terms in the expansion
    n_terms     = models.IntegerField()
    ## Regularization paraemter
    alpha       = models.FloatField()
    ## Max distance
    d_max       = models.FloatField()
    
    ## Minimum Q-value
    q_min       = models.FloatField(null=True)
    ## Maximum Q-value
    q_max       = models.FloatField(null=True)
    
    ## Time stamp
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    
    def __unicode__(self):
        desc = "D=%-5.4g" % self.d_max
        if self.q_min is not None and self.q_max is None:
            desc = desc.strip() + "; Q>%-5.4g" % self.q_min
        elif self.q_min is None and self.q_max is not None:
            desc = desc.strip() + "; Q<%-5.4g" % self.q_max
        elif self.q_min is not None and self.q_max is not None:
            desc = desc.strip() + "; Q=[%-5.4g;%-5.4g]" % (self.q_min, self.q_max)
        
        return desc

    def get_description(self):
        return self.__unicode__()
    get_description.short_description = 'Description'

    def get_file_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.iq_data.name
    get_file_name.short_description = 'File name'
        
    def get_user_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        try:
            return User.objects.get(pk=self.owner).username
        except:
            # An exception can be raised when the owner of a data set "deletes" his
            # association to that data but a link still exists for another user.
            # The data set will then appear as owned by "System" to the user with the link.
            return "System"
    get_user_name.short_description = 'User name'
        
    def get_parameters(self):
        return {'has_bck': self.has_bck,
                'slit_height': self.slit_height,
                'slit_width': self.slit_width,
                'n_terms': self.n_terms,
                'alpha': self.alpha,
                'd_max': self.d_max,
                'q_min': self.q_min,
                'q_max': self.q_max,
                }
        
    def get_results(self):
        """
            Return the PrOutput object for the output of this fit
        """
        try:
            return PrOutput.objects.get(inversion=self)
        except:
            # No such object, not a problem
            return None
        
@models.permalink
def get_absolute_url(self):
    return ('simpleplot.views.details', [str(self.id)])


        
class PrOutput(models.Model):
    """
    """
    ## Associated P(r) inversion 
    inversion = models.ForeignKey(PrInversion)
    ## Chi^2
    chi2    = models.FloatField(null=True)
    ## R_g  
    rg      = models.FloatField(null=True)
    ## Background value
    bck     = models.FloatField(null=True)
    ## I(q=0)
    iq_zero = models.FloatField(null=True)
    ## Oscillation parameter
    osc     = models.FloatField(null=True)
    ## Positive fraction
    pos_frac = models.FloatField(null=True)
    ## 1-sigma positive fraction
    pos_frac_1sigma = models.FloatField(null=True)
    
class PrCoefficients(models.Model):
    """
    """
    ## Associated P(r) output object
    proutput = models.ForeignKey(PrOutput)
    ## Coefficient type 0=coefficients, 1=covariance
    type     = models.IntegerField()
    ## Main index 
    main_index   = models.IntegerField()
    ## Secondary index 
    sec_index   = models.IntegerField(null=True)
    ## value
    value    = models.FloatField(null=True)
    
class AnonymousSharedData(models.Model):
    """
    """
    ## Key used to verify access to the data 
    shared_key = models.CharField(max_length=100, unique=True)
    ## Shared data
    iq_data = models.ForeignKey(IqData)
    
    def get_file_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.iq_data.name
    get_file_name.short_description = 'File name'
    
class AnonymousSharedPr(models.Model):
    """
    """
    ## Key used to verify access to the data 
    shared_key = models.CharField(max_length=100, unique=True)
    ## Shared P(r) inversion 
    inversion = models.ForeignKey(PrInversion)
    
    def get_file_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.inversion.get_file_name()
    get_file_name.short_description = 'File name'
    
    
class UserSharedData(models.Model):
    """
        Hard link between a data set and a user that is not the original owner.
        Once a user clicks on the anonymous link to get access to the data,
        he will be given the opportunity to 'store' this data in his shared
        data folder.
    """
    ## Shared data
    iq_data = models.ForeignKey(IqData)
    ## User who has access to this data
    user    = models.ForeignKey(User)
    
    def get_file_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.iq_data.name
    get_file_name.short_description = 'File name'
    
    def get_user_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.user.username
    get_user_name.short_description = 'User name'
    
class UserSharedPr(models.Model):
    """
        Hard link between a data set and a user that is not the original owner.
        Once a user clicks on the anonymous link to get access to the data,
        he will be given the opportunity to 'store' this data in his shared
        data folder.
    """
    ## Shared pr inversion
    inversion = models.ForeignKey(PrInversion)
    ## User who has access to this data
    user    = models.ForeignKey(User)
    
    def get_file_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.inversion.get_file_name()
    get_file_name.short_description = 'File name'
    
    def get_user_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.user.username
    get_user_name.short_description = 'User name'
    
