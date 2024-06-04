from sans.dataloader.data_info import Data1D
from sans.models import qsmearing

import copy
import numpy

"""
    TODO: refactor the whole confusion with the model names vs IDs. Only use IDs.
"""

POINT_SMEARING = 'Point smearing'
SLIT_SMEARING  = 'Slit smearing'

DEFAULT_SMEARING_ID = 1
POINT_SMEARING_ID   = 2
SLIT_SMEARING_ID    = 3


# Smearing models
_smearing_options = dict(
                 none    = dict(id=0, name="None"),
                 default = dict(id=DEFAULT_SMEARING_ID, name="Data default"),
                 point   = dict(id=POINT_SMEARING_ID, name=POINT_SMEARING),
                 slit    = dict(id=SLIT_SMEARING_ID, name=SLIT_SMEARING)
                 )


class BaseSmearerAdapter(object):
    ## List of smearing parameters
    smearing_parameters = []
    ## False if the smearing parameters are considered variables
    is_fixed = True
    ## Model name
    name = ''
    ## ID number
    id = None
    
    def __init__(self, smearer=None, fit_parameters={}, is_fixed=False):
        # If a smearer object is given, check that it is of the right class
        self._check_smearer_class(smearer)
        self.is_fixed = is_fixed
        
        # Check the if a parameter set is given that it is a dict
        if fit_parameters is not None and type(fit_parameters) != dict:
            raise ValueError, "Smearer adapters can only be instantiated with a parameter dictionary"
        
        if smearer is not None and type(fit_parameters)==dict and len(fit_parameters)>0:
            raise ValueError, "Smearer adapters can only be instantiated with _either_ a smearer object or a parameter dict"
        
        # If a smearer object is given, process it to extract its smearing parameters
        if smearer is not None:
            self.smearing_parameters = self._get_parameters_from_smearer(smearer)
        # If a fit problem parameter dict is given, process it to extract its smearing parameters
        else:
            self.smearing_parameters = self._get_parameters(fit_parameters)
        
    def _get_parameters(self, default_values=None): return NotImplemented
    def _get_parameters_from_smearer(self, smearer): return NotImplemented
    def _check_smearer_class(self, smearer): return NotImplemented

    def get_smearing_parameters(self):
        """
            Returns a copy of the smearing parameters
        """
        return copy.deepcopy(self.smearing_parameters)
    
    def get_formatted_smearing_parameters(self):
        return copy.deepcopy(self.smearing_parameters)
            
    def get_smearing_parameters_as_list(self):
        """
            Returns a list of the names of the smearing parameters
        """
        params = []
        for item in self.smearing_parameters:
            params.append(copy.deepcopy(item['short_name']))
        return params 

    def get_smearer(self): return NotImplemented
        
    def process_model_parameter_list(self, smearing_parameters):
        """
            Process a list of parameters and re-initialize the adapter
        """
        self.smearing_parameters = self._get_parameters()
        for p in smearing_parameters:
            for _p in self.smearing_parameters:
                if p['short_name'] == _p['short_name']:
                    _p['value']   = p['value']      
        
class PointSmearerAdapter(BaseSmearerAdapter):
    dq = None
    id = POINT_SMEARING_ID
    name = POINT_SMEARING
    
    def __init__(self, smearer=None, fit_parameters={}, is_fixed=False):
        super(PointSmearerAdapter, self).__init__(smearer=smearer, fit_parameters=fit_parameters, is_fixed=is_fixed)
        
    def _check_smearer_class(self, smearer):
        if smearer is not None and not isinstance(smearer, qsmearing.QSmearer):
            raise RuntimeError, "SlitSmearerAdapter can only take a QSmearer object"
        
    def _get_parameters(self, default_values=None):
        if default_values is None:
            default_values = {}
        elif type(default_values) != dict:
            raise ValueError, "PointSmearerAdapter._get_parameters expects a dictionary"
        
        if self.is_fixed:
            min_width = default_values.get('smear_dq_min', 0)
            max_width = default_values.get('smear_dq_max', 0)
            avg_width = default_values.get('smear_dq_avg', 0)
            return self._get_summary_parameters(min_width, max_width, avg_width) 
        else:
            item = 'smear_dq'
            value = default_values.get(item, 0)
            
            # Store the dq parameter
            self.dq = dict(short_name=item,
                        long_name='&Delta;Q',
                        units='1/&#197;',
                        value=value,
                        help='Q resolution',
                        error=0,
                        checked=False)
            
            return [self.dq]

        
    def _get_parameters_from_smearer(self, smearer):
        """
            Returns the smearing parameters from an actual QSmearer object.
            Since deltaQ is an array, we return the min/avg/max. 
        """
        if smearer is None:
            raise RuntimeError, "SlitSmearerAdapter: smearer not set"

        min_width = min(smearer.width)
        max_width = max(smearer.width)
        avg_width = sum(smearer.width)/len(smearer.width)
        
        return self._get_summary_parameters(min_width, max_width, avg_width)

    
    def _get_summary_parameters(self, min_width, max_width, avg_width):
        """
            Format summary parameters
        """
        params = []
        params.append(dict(short_name='smear_dq_min',
                    long_name='&Delta;Q min',
                    units='1/&#197;',
                    value=min_width,
                    help='Minimum Q resolution',
                    error=0,
                    checked=False))

        params.append(dict(short_name='smear_dq_avg',
                    long_name='&Delta;Q avg',
                    units='1/&#197;',
                    value=avg_width,
                    help='Average Q resolution',
                    error=0,
                    checked=False))

        params.append(dict(short_name='smear_dq_max',
                    long_name='&Delta;Q max',
                    units='1/&#197;',
                    value=max_width,
                    help='Maximum Q resolution',
                    error=0,
                    checked=False))
        
        return params
    
    def get_smearer(self, data1D):
        """
            Returns a QSmearer object for the supplied Data1D
            object. 
            
            @param data1D: Data1D object
        """
        smearer = qsmearing.QSmearer(data1D)
        
        # Set point resolution
        if self.dq is not None: 
            smearer.width = numpy.asarray(len(data1D.x)*[self.dq['value']])

        return smearer
    
    
class SlitSmearerAdapter(BaseSmearerAdapter):
    width = None
    height = None
    id = SLIT_SMEARING_ID
    name = SLIT_SMEARING
    
    def __init__(self, smearer=None, fit_parameters={}, is_fixed=False):
        super(SlitSmearerAdapter, self).__init__(smearer=smearer, fit_parameters=fit_parameters, is_fixed=is_fixed)

    def _check_smearer_class(self, smearer):
        if smearer is not None and not isinstance(smearer, qsmearing.SlitSmearer):
            raise RuntimeError, "SlitSmearerAdapter can only take a SlitSmearer object"
        
    def _get_parameters_from_smearer(self, smearer):
        if smearer is None:
            raise RuntimeError, "SlitSmearerAdapter: smearer not set"
        return self._get_parameters(dict(smear_width=smearer.width,
                                        smear_height=smearer.height,
                                        ))
    
    def get_smearer(self, data1D):
        """
            Returns a SlitSmearer object for the supplied Data1D
            object. 
            
            @param data1D: Data1D object
        """
        smearer = qsmearing.SlitSmearer(data1D)
        
        # Set slit geometry if available
        if self.width is not None: smearer.width = self.width['value']
        if self.height is not None: smearer.height = self.height['value']
            
        return smearer
        
    def _get_parameters(self, form_data=None):
        """
            Returns the parameter set for slit smearing.
            If values are provided, they will override the defaults.
        """
        if form_data is None:
            form_data = {}
        elif type(form_data) != dict:
            raise ValueError, "SlitSmearerAdapter._get_parameters expects a dictionary"
        
        value = 0
        item = "smear_width"
        value = form_data.get(item, 0) 
        # Store the slit width
        self.width = dict(short_name=item,
                    long_name='Width',
                    units='1/&#197;',
                    value=value,
                    help='Slit width',
                    error=0,
                    checked=False)
        
        
        item = "smear_height"
        value = form_data.get(item, 0) 
        # Store the slit height
        self.height = dict(short_name=item,
                    long_name='Height',
                    units='1/&#197;',
                    value=value,
                    help='Slit height',
                    error=0,
                    checked=False)
  
        return [self.width, self.height]

def get_default_smearer(data_info):
    """
        Returns the default smearer from the information found in the data
        TODO: make this part of the SmearingAdapters.
    """
    return qsmearing.smear_selection(data_info)

def get_smearing_model_id_by_name(smearing_model):
    """
        Returns the ID of a smearing model according to the given model name.
    """
    if smearing_model == POINT_SMEARING:
        return POINT_SMEARING_ID
    elif smearing_model == SLIT_SMEARING:
        return SLIT_SMEARING_ID
    else:
        return None

def get_smearing_model_name_by_id(smearing_model_id):
    """
        Returns the ID of a smearing model according to the given model name.
    """
    if smearing_model_id == POINT_SMEARING_ID:
        return POINT_SMEARING
    elif smearing_model_id == SLIT_SMEARING_ID:
        return SLIT_SMEARING
    else:
        return None

def get_smear_adapter_from_id(smearer_model_id, form_data={}):
    """
        Get smearing adapter for the given smearing model type ID
        @param smearer_model_id: smearing model type ID
    """
    if smearer_model_id == POINT_SMEARING_ID:
        return PointSmearerAdapter(fit_parameters=form_data)
    elif smearer_model_id == SLIT_SMEARING_ID:
        return SlitSmearerAdapter(fit_parameters=form_data)
    else:
        return None

def get_default_smear_adapter(data1d):
    """
        Returns the default smearing adapter for the given data set
    """
    smearer = qsmearing.smear_selection(data1d)

    if isinstance(smearer, qsmearing.QSmearer):
        return PointSmearerAdapter(smearer, is_fixed=True)
    elif isinstance(smearer, qsmearing.SlitSmearer):
        return SlitSmearerAdapter(smearer, is_fixed=True)
    else:
        return None
    
def get_smear_adapter_class_by_type(smearer_model_id):
    """
        Returns the smear adapter class correspinding smearing type
    """
    if smearer_model_id == POINT_SMEARING_ID:
        return PointSmearerAdapter
    elif smearer_model_id == SLIT_SMEARING_ID:
        return SlitSmearerAdapter
    else:
        return None


    
