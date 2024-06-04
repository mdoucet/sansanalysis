import time, hashlib

# Django dependencies
from django.db.models import Q
from django.core.urlresolvers import reverse

# Application dependencies
from sansanalysis.simpleplot.models import IqData
import sansanalysis.simpleplot.manipulations.iqdata as iqdata

# Application imports
from sansanalysis.modeling.models import FitProblem, TheoryModel, ModelParameter, ModelParameterName
from sansanalysis.modeling.models import SmearingModel, SmearingModelInfo, SmearingModelParameter
from sansanalysis.modeling.models import UserSharedFit, AnonymousSharedFit
import sans_model_adapter, smearing_model_adapter

#TODO: this belong in a utility module
def get_data(iq_id):
    iq = IqData.objects.get(pk=iq_id)
    loader = iqdata.FileDataLoader()
    data_info = loader.load_file_data(iq)
    if data_info is None:
        error_msg = "Could not read file [iq_id=%s]." % str(iq.id)
        store_error(user=None, url=None, text=error_msg, method='modeling.data_manipulations.get_data', build=sansanalysis.settings.APP_VERSION)
        raise RuntimeError, "Data loader could not read the data file [ID=%s]." % str(iq.id)
    return data_info



def compute_model(fit_problem, iq_id):
    data_info = get_data(iq_id)
    return sans_model_adapter.compute_model(fit_problem, iq_id, data_info)
    
def perform_fit(fit_problem, iq_id):
    data_info = get_data(iq_id)
    sans_model_adapter.perform_fit(fit_problem, iq_id, data_info)
    return fit_problem.chi2
    
def store_fit_problem(user, fit_problem):
    """
        Store a fit problem
        
        @param user: User objects
        @param fit_problem: sans_model_adapter.FitProblem object
    """
    # Theory model
    model = TheoryModel(model_id = fit_problem.model_id,
                        name     = fit_problem.model_name)
    model.save()
    
    # Parameters for the theory model
    for p in fit_problem.model_parameters:
        try:
            name = ModelParameterName.objects.get(name=p['short_name'])
        except ModelParameterName.DoesNotExist:
            name = ModelParameterName(name=p['short_name'])
            name.save()
        
        p = ModelParameter(model=model, name=name, 
                           value=p['value'], error=p['error'], 
                           dispersion=None, is_fixed=(not p['checked']))
        p.save()
    
    # Data set
    iq_data = IqData.objects.get(pk=fit_problem.data_id)
    
    # Smearing option, as selected by the user
    smearing_option = 0
    if fit_problem.smearer_option_id is not None:
        smearing_option = fit_problem.smearer_option_id
    
    # Smearing model
    smearing_model = None
    if fit_problem.smearer_model_id is not None:
        smearing_model_id = smearing_model_adapter.get_smearing_model_id_by_name(fit_problem.smearer_model_id)
        if smearing_model_id is not None:
            smearing_model_info = SmearingModelInfo.objects.get(model_id=smearing_model_id)
            smearing_model = SmearingModel(model_info=smearing_model_info)
            smearing_model.save()
        
    # Smearing model parameters
    if fit_problem.smear_adapter is not None:
        for p in fit_problem.smear_adapter.get_smearing_parameters():
            try:
                name = ModelParameterName.objects.get(name=p['short_name'])
            except ModelParameterName.DoesNotExist:
                name = ModelParameterName(name=p['short_name'])
                name.save()
                
            p = SmearingModelParameter(model=smearing_model, name=name, value=p['value'])
            p.save()
        
    # Overall fit problem
    fp = FitProblem(iq_data=iq_data, model=model, owner=user,
                    chi2=fit_problem.chi2, q_min=fit_problem.qmin, q_max=fit_problem.qmax,
                    smearing_option=smearing_option, smearing_model=smearing_model)
    fp.save()
    return fp

def restore_fit_problem(fit_id):
    """
        Restore a fit problem from the database
        
        @param fit_id: pk of the fit object
        @return: sans_model_adapter.FitProblem object
    """
    # Get the overall fit problem
    fp = FitProblem.objects.get(pk=fit_id)

    fit_problem = sans_model_adapter.FitProblem(data_id=fp.iq_data.id, model_id=fp.model.model_id, 
                                                qmin=fp.q_min, qmax=fp.q_max)

    # Extra fit problem data members
    fit_problem.chi2 = fp.chi2
    fit_problem.model_name = fp.model.name
    
    # Get the model parameters
    model_parameters = []
    for p in ModelParameter.objects.filter(model=fp.model):
        par = sans_model_adapter.get_empty_parameter_dict()
        par['short_name'] = p.name.name
        par['value'] = p.value
        par['error'] = p.error
        par['checked'] = not p.is_fixed
        model_parameters.append(par)
        
    # Process the newly created parameter list
    fit_problem.process_model_parameter_list(model_parameters)
       
    # Smearing option, as selected by the user
    fit_problem.smearer_option_id = fp.smearing_option
    
    # Smearing model
    if fp.smearing_model is not None:
        fit_problem.smearer_model_id = smearing_model_adapter.get_smearing_model_name_by_id(fp.smearing_model.model_info.model_id)
        
        # Smearing model parameters
        smearing_model_parameters = []
        for p in SmearingModelParameter.objects.filter(model=fp.smearing_model):
            par = sans_model_adapter.get_empty_parameter_dict()
            par['short_name'] = p.name.name
            par['value'] = p.value
            smearing_model_parameters.append(par)
        
        # Create smear_adapter
        is_fixed = fit_problem.smearer_option_id == smearing_model_adapter.DEFAULT_SMEARING_ID
        fit_problem.smear_adapter = smearing_model_adapter.get_smear_adapter_class_by_type(fp.smearing_model.model_info.model_id)(is_fixed=is_fixed)
        if fit_problem.smear_adapter is not None:
            fit_problem.smear_adapter.process_model_parameter_list(smearing_model_parameters)
    
    return fit_problem
    
    
def get_recent_fits_by_iqdata(user_id, iq_id):
    """
        Get latest five data sets visited by the user
        
        Make sure that all links are available and that the user
        is either the owner of the file or has access through
        a stored link.
        
        @param user_id: user id
        @param iq_id: IqData ojbect PK
    """
    
    fits = FitProblem.objects.filter(owner__id=user_id, iq_data__id=iq_id).order_by('created_on').reverse()      
        
    recent = []
    labels = []
    for item in fits:
        label = "%s; &chi;<span class='exponent'> 2</span>=%-3.2g" % (item.model.name, item.chi2)
        if label not in labels and len(recent)<5:
            labels.append(label)
            recent.append({'name':label,
                           'time':item.created_on,
                           'url':reverse('sansanalysis.modeling.views.fit', args=(item.iq_data.id,
                                                                                   item.id,))})            
    return recent
          
  
def get_recent_fits_by_user(user_id):
    """
        Get latest five data sets visited by the user
        
        Make sure that all links are available and that the user
        is either the owner of the file or has access through
        a stored link.
        
        @param user_id: user id
    """
    
    fits = FitProblem.objects.filter(owner__id=user_id).order_by('created_on').reverse()      
        
    recent = []
    labels = []
    for item in fits:
        label = "I(q): %s" % item.iq_data.name
        if label not in labels and len(recent)<5:
            labels.append(label)
            recent.append({'name':label,
                           'time':item.created_on,
                           'url':reverse('sansanalysis.modeling.views.fit', args=(item.iq_data.id,
                                                                                   item.id,))})            
    return recent
          

def get_fit_shared_key(fit, create=False):
    """
        Get a key for a given FitProblem object to be shared.
        @param iq: FitProblem object
        @param create: if True, a link will be created if none is found
    """
    keys = AnonymousSharedFit.objects.filter(fit=fit)
    if len(keys)==0:
        if create:
            key = hashlib.md5("%s%f" % (fit.id, time.time())).hexdigest()
            key_object = AnonymousSharedFit(shared_key=key, fit=fit)
            key_object.save()
            return key
        else:
            return None
    else: 
        return keys[0].shared_key    
    

def get_anonymous_shared_fit(key):
    """
        Retrieve FitProblem object by key
        @param key: shared key 
    """
    shared_data = AnonymousSharedFit.objects.filter(shared_key=key)
    if len(shared_data)==1:
        return shared_data[0].fit
    elif len(shared_data)>1:
        raise RuntimeError, "data_manipulations.get_anonymous_shared_fit: shared_key not unique!"
    return None
          
def deactivate_fit(fit):
    """
        Deactivate a FitProblem fit. Since many tables have FitProblem foreign keys, 
        we do not delete the data set. We simply change the owner to user ID = 0.
        That will prevent the data set to ever show up in the user's list of
        data and he will lose access to it.
        This solution will also enable a shared I(q) fit to remain with
        the users it was shared with.
        
        Return true if we removed shared links
    """
    fit.owner = None
    fit.save()
    return False          

def has_shared_fit(user, fit):
    """
        Returns True if the specified user has a shared data link
        to the specified FitProblem object.
        @param iq: FitProblem object
        @param user: User object
    """
    shared = UserSharedFit.objects.filter(fit=fit, user=user)
    return len(shared)>0

  
def create_shared_link(user, fit):
    """
        Create a UserShareFit link between the user
        and a FitProblem object if it doesn't already exist
        
        Returns the link
    """
    # Verify that the link doesn't already exist
    old_shared = UserSharedFit.objects.filter(fit=fit, user=user)
    if len(old_shared)==0:
        shared = UserSharedFit(fit=fit, user=user)
        shared.save()
        return shared
    else:
        return old_shared[0]
          

def remove_shared_link(fit, user=None):
    """
        Remove all links to a fit.
        If a user is specified, remove links only for this user.
    """
    if user is None:
        shared = UserSharedFit.objects.filter(fit=fit)
    else:
        shared = UserSharedFit.objects.filter(fit=fit, user=user)
    
    has_links = len(shared)>0
    
    # Delete the links
    shared.delete()

    return has_links

def get_model_list():
    return []
          