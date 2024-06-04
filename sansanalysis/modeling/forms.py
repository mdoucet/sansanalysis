"""
  Form for reflectivity inversion
"""
import math, sys
from django import forms
from django.template import Context, loader
from numpy import isnan


# Application imports
import sans_model_adapter
import smearing_model_adapter
import data_manipulations

class FormattedInput(forms.TextInput):
     input_type = 'text'
 
     def __init__(self, *args, **kwargs):
         super(FormattedInput, self).__init__(*args, **kwargs)
 
     def render(self, name, value, attrs=None):
         
         try:
             formatted_value = "%g" % value
         except:
             formatted_value = value
         return super(FormattedInput, self).render(name, formatted_value, attrs)
     
SMEARING_CHOICES = [[0,'None'], [1,'Data default'], [2, smearing_model_adapter.POINT_SMEARING], [3, smearing_model_adapter.SLIT_SMEARING]]

class ModelForm(forms.Form):
    """
        Specify a theory model for fitting
    """
    ## Theory model selection
    model  = forms.ChoiceField(label="Model", choices=sans_model_adapter.get_models_as_list(),
                               widget=forms.HiddenInput(attrs={'title':"Select a model to fit your data",
                                                                 'onchange':"show_parameters()"}))
       
    # Minimum Q-value
    q_min       = forms.FloatField(label='Q min [1/&Aring;]', widget=forms.TextInput(attrs={'title':"Minimum Q-value of the data used in the fit",
                                                                                 'onchange':"process_par_change()"}))
    # Maximum Q-value
    q_max       = forms.FloatField(label='Q max [1/&Aring;]', widget=forms.TextInput(attrs={'title':"Maximum Q-value of the data used in the fit",
                                                                                 'onchange':"process_par_change()"})) 
       
    # Smearing type
    smearing    = forms.IntegerField(required=True)
    smear_type  = forms.CharField(max_length=20, required=False)                                   
       
    def setFields(self, kwds):
        """
            Set the fields in the form
        """
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.fields[k] = kwds[k]
            
    def setData(self, kwds):
        """
            Set the data to include in the form
        """
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.data[k] = kwds[k]
            
    def clean(self):
        cleaned = super(ModelForm, self).clean()

        for name,field in self.fields.items():
            if isinstance(field, forms.fields.FloatField):
                if self.cleaned_data.has_key(name) \
                    and isnan(self.cleaned_data[name]):
                    self.errors[name] = "Enter a whole number."
        
        return cleaned

def model_parameters_as_list(model_id):
    params = []
    # Get the model as an object (sans.models parameters are only populated at instantiation)
    d = sans_model_adapter.get_model_parameters(model_id)
    for item in d:
        params.append(item['short_name'])

    return params
    

def model_parameters_as_xml(model_id):
    """
        Method that returns an XML list of parameters for a given model.
    """
    params = '<model>%s</model>' % sans_model_adapter.get_model_name_by_id(model_id)
    # Get the model as an object (sans.models parameters are only populated at instantiation)
    d = sans_model_adapter.get_model_parameters(model_id)
    for item in d:
        params += '<par>%s</par>' % item['short_name']

    return params

def smearing_parameters_as_xml(model_id, smearer_fixed=False):
    """
        Method that returns an XML list of parameters for a given smearing model.
    """
    params = ''
    # Get the model as an object (sans.models parameters are only populated at instantiation)
    smear_adapter_cls = smearing_model_adapter.get_smear_adapter_class_by_type(model_id)
    if smear_adapter_cls is not None:
        smear_adapter = smear_adapter_cls(is_fixed=smearer_fixed)
        d = smear_adapter.get_smearing_parameters()
        
        for item in d:
            params += '<par>%s</par>' % item['short_name']

    return params

def model_parameters_as_table(model_id, user_values=None):
    """
        Returns an HTML table with the parameters of the specified model.
    """
    d = sans_model_adapter.get_model_parameters(model_id, user_values)
    t = loader.get_template('modeling/model_parameters.html')
    c = Context({
        'params': d,
    })
    return t.render(c)
        
def _model_as_form_parameters(model_id):
    
    d = sans_model_adapter.get_model_parameters(model_id)
    model_pars = {}
    for item in d:
        # Check box
        chk_name = 'chk_%s' % item['short_name']
        model_pars[chk_name] = forms.BooleanField(label=chk_name, required=False)
        # Parameter input
        model_pars[item['short_name']] = forms.FloatField(label=item['short_name'])
    
    return model_pars
    
def _smearer_as_form_parameters(model_id, smearer_fixed=False):
    """
        Returns a dictionary of smearing model parameters
        @param model_id: smearing model id
    """
    smearer_id = smearing_model_adapter.get_smearing_model_id_by_name(model_id)
    
    model_pars = {}   
    smear_adapter_cls = smearing_model_adapter.get_smear_adapter_class_by_type(smearer_id)
    if smear_adapter_cls is not None:
        smear_adapter = smear_adapter_cls(is_fixed=smearer_fixed, fit_parameters={})
        d = smear_adapter.get_smearing_parameters()
        if type(d) == list:
            for item in d:
                # Parameter input
                model_pars[item['short_name']] = forms.FloatField(label=item['short_name'])
        
    return model_pars
    
        
def populate_fit_problem_from_query_data(query_data, fit_problem=None):
    """
        Populates a fit problem from raw query data (uncleaned).
        
        @param fit_problem: sans_model_adapter.FitProblem object
        @return: return the form corresponding to the query data
    """
    if fit_problem is None:
        fit_problem  = sans_model_adapter.FitProblem()
    
    model_id = query_data.get('model', default=0)
    smearer_model_id = query_data.get('smear_type', default=None)
    try:
        smearing_option_id = int(query_data.get('smearing', default=None))
    except:
        smearing_option_id = None
    
    # Create a form so that we can validate the data
    form = ModelForm(query_data)

    # Check against the default smearing option, for which the parameters are fixed
    is_fixed = smearing_option_id == smearing_model_adapter.DEFAULT_SMEARING_ID
        
    _populate_fit_form(form, model_id, smearer_model_id, is_fixed)
    
    if form.is_valid(): 
        fit_problem.is_valid = True 
        populate_fit_problem_from_form_data(fit_problem, form.cleaned_data)       
                
    return form

def populate_fit_problem_from_form_data(fit_problem, form_data):
    """
        Populate a FitProblem object from clean form data
    """
    if type(form_data) != dict:
        return
  
    # Get the model ID
    if form_data.has_key('model'): 
        model_id = int(form_data['model'])
        fit_problem.model_id = model_id
        fit_problem.model_name = sans_model_adapter.get_model_name_by_id(fit_problem.model_id)
    
    # Look for Q range, if available
    if form_data.has_key('q_min') and form_data['q_min']>=0:
        fit_problem.qmin = form_data['q_min']
    if form_data.has_key('q_max') and form_data['q_max']>0:
        fit_problem.qmax = form_data['q_max']

    # Model parameters
    fit_problem.model_parameters = sans_model_adapter.get_model_parameters(fit_problem.model_id)
    for p in fit_problem.model_parameters:
        # If a parameter is part of the query data, take its value from the query data
        if form_data.has_key(p['short_name']): 
            p['value'] = form_data[p['short_name']]
        if form_data.has_key("chk_%s" % p['short_name']): 
            p['checked'] = form_data["chk_%s" % p['short_name']]

    # Smearing information
    if form_data.has_key('smearing'): 
        fit_problem.smearer_option_id = form_data['smearing']
    if form_data.has_key('smear_type'): 
        fit_problem.smearer_model_id = form_data['smear_type']


    # Get the parameter set for the smearing model we have
    fit_problem.smear_adapter = get_smear_adapter_from_form_data(form_data)
                
def get_smear_adapter_from_form_data(form_data):
    """
        Returns a smearing adapter object as described by the form data.
    """
    ## Smearing model ID
    smearer_model_id = None
    ## Smearing option [tells us whether the model was chosen by the user or not]
    smearer_option_id = None
    
    if form_data.has_key('smearing'): 
        smearer_option_id = form_data['smearing']
    if form_data.has_key('smear_type'): 
        smearer_model_id = form_data['smear_type']
        
    # Check against the default smearing option, for which the parameters are fixed
    is_fixed = smearer_option_id == smearing_model_adapter.DEFAULT_SMEARING_ID
        
    #TODO: check that smearing and smear_type are compatible with the same smearer class
    if smearer_model_id == smearing_model_adapter.POINT_SMEARING:
        return smearing_model_adapter.PointSmearerAdapter(fit_parameters=form_data, is_fixed=is_fixed)
    elif smearer_model_id == smearing_model_adapter.SLIT_SMEARING:
        return smearing_model_adapter.SlitSmearerAdapter(fit_parameters=form_data, is_fixed=is_fixed)
    else:
        return None
                
                            
            
            
def _populate_fit_form(form, model_id, smearer_id=None, smearer_fixed=False):
    """
        Populates a fit form with model and smearing parameters
        @param model_id: model ID
        @param smearer_id: smearing model ID
    """
    # Add model parameters
    model_pars = _model_as_form_parameters(model_id)
    form.setFields(model_pars)
    # Add smearing parameters
    model_pars = _smearer_as_form_parameters(smearer_id, smearer_fixed)
    form.setFields(model_pars)

def fit_problem_as_form(fit_problem):
    """    
        Returns a form for a specific fit problem.
        
        @param fit_problem: FitProblem object
        @return: ModelForm object
    """
    form = ModelForm(fit_problem_as_form_data(fit_problem))
    
    # Determine the smear model, but only if we are not using the 
    # default smearing information from the data and we need controls
    # for the smearing parameters
    smearer_id = fit_problem.smearer_model_id
    is_fixed = (fit_problem.smearer_option_id == smearing_model_adapter.DEFAULT_SMEARING_ID)
        
    _populate_fit_form(form, fit_problem.model_id, smearer_id, is_fixed)
    return form

def fit_problem_as_form_data(fit_problem):
    """
        Returns a dictionary of parameters that can be fed to a ModelForm
        @param fit_problem: FitProblem object
    """
    # Basic modeling information
    parameters = {}
    parameters['model'] = fit_problem.model_id
    parameters['smearing'] = fit_problem.smearer_option_id
    parameters['smear_type'] = fit_problem.smearer_model_id

    # Model parameters
    for p in fit_problem.model_parameters:
        parameters[p['short_name']] = p['value']
        parameters["chk_%s" % p['short_name']] = p['checked']    

    # Q range
    parameters['q_min'] = fit_problem.qmin
    parameters['q_max'] = fit_problem.qmax
    
    # Smearing parameters
    if fit_problem.smear_adapter is not None:
        parameters.update(smear_adapter_as_form_data(fit_problem.smear_adapter))
    
    return parameters
    
    
def smear_adapter_as_form_data(smear_adapter):
    """
        Returns a dictionary of parameters that can be fed to a ModelForm
        and fit template.
        @param smear_adapter: BaseSmearerAdapter object
    """
    parameters = {}
    
    
    parameters['smear_type'] = smear_adapter.name
    parameters['smearing']   = smear_adapter.id
    if smear_adapter.is_fixed:
        parameters['smearing'] = smearing_model_adapter.DEFAULT_SMEARING_ID
        
    
    smear_pars = smear_adapter.get_smearing_parameters()
    for p in smear_pars:
        parameters[p['short_name']] = p['value']

    return parameters
        
        
        
        
    
    