# Django imports
from django.db import models
from django.contrib.auth.models import User

# Application imports
from sansanalysis.simpleplot.models import IqData

    
class TheoryModel(models.Model):
    """
        SANS theory model
    """
    ## Model ID
    model_id   = models.IntegerField()
    
    ## User-specified name (optional)
    name       = models.CharField(max_length=100, null=True)
    
    ## Time stamp
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)

    def get_model_name(self):
        """
            Return the name of the model
        """
        return self.name
    get_model_name.short_description = 'Name'
        

class DispersionModel(models.Model):
    """
        Dispersion model
    """
    ## Model ID
    model_id   = models.IntegerField()       
    
class ModelParameterName(models.Model):
    """
        Table of parameter names
    """
    ## Parameter name
    name       = models.CharField(max_length=100)
    
class ModelParameter(models.Model):
    """
        A model parameter. Can be input (fixed) or output.
    """    
    ## Model this parameter belongs to
    model      = models.ForeignKey(TheoryModel)
    
    ## Parameter name
    name       = models.ForeignKey(ModelParameterName)
    
    ## Value
    value      = models.FloatField(null=True)
    
    ## Error on the value
    error      = models.FloatField(null=True)
    
    ## If set to a model, the parameter is dispersed, as opposed to being a float value
    dispersion = models.ForeignKey(DispersionModel, null=True)
    
    ## True if the parameter is fixed, as opposed to being a fit parameter
    is_fixed = models.BooleanField(default=True)
  
    def get_model_id(self):
        """
            Return the id of the model
        """
        return self.model.model_id
    get_model_id.short_description = 'Model id'

    def get_name(self):
        """
            Return the name of the parameter
        """
        return self.name.name
    get_name.short_description = 'Name'


class SmearingModelInfo(models.Model):
    """
        Table of dispersion model names
    """
    ## Model ID
    model_id = models.IntegerField()
    ## Model name
    name     = models.CharField(max_length=100)
    

class SmearingModel(models.Model):
    """
        Smearing model
    """
    ## Static model info
    model_info = models.ForeignKey(SmearingModelInfo)
    
    
class SmearingModelParameter(models.Model):
    """
        A model parameter. Can be input (fixed) or output.
    """    
    ## Model this parameter belongs to
    model      = models.ForeignKey(SmearingModel)
    
    ## Parameter name
    name       = models.ForeignKey(ModelParameterName)
    
    ## Value
    value      = models.FloatField(null=True)
    
    
class DispersionParameter(models.Model):
    """
        A model parameter. Can be input (fixed) or output.
    """    
    ## Model this parameter belongs to
    model      = models.ForeignKey(DispersionModel)
    
    ## Value
    value      = models.FloatField(null=True)
    
    ## Error on the value
    error      = models.FloatField(null=True)
    
    ## True if the parameter is fixed, as opposed to being a fit parameter
    is_fixed = models.BooleanField(default=True)
  
        
        
class FitProblem(models.Model):
    """
        A fit. A fit is a model, a data set, and outputs
    """
    ## Model used for this fit
    model      = models.ForeignKey(TheoryModel)
    ## Fitted data
    iq_data    = models.ForeignKey(IqData)    
    ## Chi squared    
    chi2       = models.FloatField(null=True)
    ## Q min
    q_min      = models.FloatField(null=True)
    ## Q max
    q_max      = models.FloatField(null=True)
    ## Model owner
    owner      = models.ForeignKey(User, null=True)
    ## Smearing option
    smearing_option = models.IntegerField()
    ## Smearing model
    smearing_model  = models.ForeignKey(SmearingModel, null=True)
    
    ## Time stamp
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
            
    def get_user_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        if self.owner is not None:
            return self.owner.username
        else:
            # An exception can be raised when the owner of a data set "deletes" his
            # association to that data but a link still exists for another user.
            # The data set will then appear as owned by "System" to the user with the link.
            return "System"
    get_user_name.short_description = 'User name'
    
    def get_model_name(self):
        """
            Return the name of the model
        """
        return self.model.get_model_name()
    get_model_name.short_description = 'Model name'
    
    def get_data_name(self):
        """
            Return the name of the data set
        """
        return self.iq_data.name
    get_data_name.short_description = 'File name'
    
    
class AnonymousSharedFit(models.Model):
    """
        Table of shared keys for FitProblem objects
    """
    ## Key used to verify access to the data 
    shared_key = models.CharField(max_length=100, unique=True)
    ## Shared Fit
    fit = models.ForeignKey(FitProblem)
    
    def get_file_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.fit.get_data_name()
    get_file_name.short_description = 'File name'


class UserSharedFit(models.Model):
    """
        Hard link between a data set and a user that is not the original owner.
        Once a user clicks on the anonymous link to get access to the data,
        he will be given the opportunity to 'store' this data in his shared
        data folder.
    """
    ## Shared Fit
    fit = models.ForeignKey(FitProblem)
    ## User who has access to this data
    user    = models.ForeignKey(User)
    
    def get_file_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.fit.get_data_name()
    get_file_name.short_description = 'File name'
    
    def get_user_name(self):
        """
            Return the name of the file when it was originally loaded
        """
        return self.user.username
    get_user_name.short_description = 'User name'
    

