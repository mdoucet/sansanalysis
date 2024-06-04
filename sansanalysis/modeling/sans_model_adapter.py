"""
    This module will interface with the sans.models module.
    
    The sans.models module is considered in flux.
    This module isolates the sans.models module. No call to sans.models, or knowledge
    or the sans.models API should be seen outside this module.
"""
import numpy, sys, math, copy
    
from scipy import optimize

# SANS imports
from sans.models.SphereModel import SphereModel
from sans.models.CylinderModel import CylinderModel
from sans.models.FractalModel import FractalModel

        
from sans.models.CoreShellModel import CoreShellModel
from sans.models.VesicleModel import VesicleModel
from sans.models.MultiShellModel import MultiShellModel
from sans.models.BinaryHSModel import BinaryHSModel
from sans.models.CoreShellCylinderModel import CoreShellCylinderModel
from sans.models.HollowCylinderModel import HollowCylinderModel
from sans.models.FlexibleCylinderModel import FlexibleCylinderModel
from sans.models.StackedDisksModel import StackedDisksModel
from sans.models.ParallelepipedModel import ParallelepipedModel
from sans.models.EllipticalCylinderModel import EllipticalCylinderModel
from sans.models.EllipsoidModel import EllipsoidModel
from sans.models.CoreShellEllipsoidModel import CoreShellEllipsoidModel
from sans.models.TriaxialEllipsoidModel import TriaxialEllipsoidModel
from sans.models.LamellarModel import LamellarModel
from sans.models.LamellarFFHGModel import LamellarFFHGModel
from sans.models.LamellarPSModel import LamellarPSModel
from sans.models.LamellarPSHGModel import LamellarPSHGModel

##shape-independent models
from sans.models.BEPolyelectrolyte import BEPolyelectrolyte
from sans.models.DABModel import DABModel
from sans.models.GuinierModel import GuinierModel
from sans.models.DebyeModel import DebyeModel
from sans.models.PorodModel import PorodModel
from sans.models.PeakGaussModel import PeakGaussModel
from sans.models.PeakLorentzModel import PeakLorentzModel
from sans.models.FractalAbsModel import FractalAbsModel
from sans.models.LorentzModel import LorentzModel
from sans.models.PowerLawAbsModel import PowerLawAbsModel
from sans.models.TeubnerStreyModel import TeubnerStreyModel
from sans.models.LineModel import LineModel

# Application imports
from sans_fit import SansFit, Parameter
import smearing_model_adapter

# Model dictionary
_SHAPE = "Shape-Based Models"
_SHAPE_INDEP = "Shape-Independent Models"

_model_categories = [_SHAPE, _SHAPE_INDEP]
_models = dict(   
                sphere             = dict(id=0, cl=SphereModel,              cat=_SHAPE, name="Sphere", help=None),
                cylinder           = dict(id=1, cl=CylinderModel,            cat=_SHAPE, name="Cylinder", help=None),
                coreshell          = dict(id=4, cl=CoreShellModel,           cat=_SHAPE, name="Core Shell", help=None),
                vesicle            = dict(id=5, cl=VesicleModel,             cat=_SHAPE, name="Vesicle", help=None),
                multishell         = dict(id=6, cl=MultiShellModel,          cat=_SHAPE, name="Multi Shell", help=None),
                coreshellcyl       = dict(id=7, cl=CoreShellCylinderModel,   cat=_SHAPE, name="Core Shell Cylinder", help=None),
                hollowcyl          = dict(id=8, cl=HollowCylinderModel,      cat=_SHAPE, name="Hollow Cylinder", help=None),
                flexiblecyl        = dict(id=9, cl=FlexibleCylinderModel,    cat=_SHAPE, name="Flexible Cylinder", help=None),
                stackeddisks       = dict(id=10, cl=StackedDisksModel,       cat=_SHAPE, name="Stacked Disks", help=None),
                parallelepiped     = dict(id=11, cl=ParallelepipedModel,     cat=_SHAPE, name="Parallelepiped", help=None),
                ellipticalcyl      = dict(id=12, cl=EllipticalCylinderModel, cat=_SHAPE, name="Elliptical Cylinder", help=None),
                ellipsoid          = dict(id=13, cl=EllipsoidModel,          cat=_SHAPE, name="Ellipsoid", help=None),
                coreshellellipsoid = dict(id=14, cl=CoreShellEllipsoidModel, cat=_SHAPE, name="Core Shell Ellipsoid", help=None),
                triaxialellipsoid  = dict(id=15, cl=TriaxialEllipsoidModel,  cat=_SHAPE, name="Triaxial Ellipsoid", help=None),
                lamellar           = dict(id=16, cl=LamellarModel,           cat=_SHAPE, name="Lamellar", help=None),
                lamellarffh        = dict(id=17, cl=LamellarFFHGModel,       cat=_SHAPE, name="Lamellar FFHG", help=None),
                lamellarps         = dict(id=18, cl=LamellarPSModel,         cat=_SHAPE, name="Lamellar PS", help=None),
                lamellarpshg       = dict(id=19, cl=LamellarPSHGModel,       cat=_SHAPE, name="Lamellar PSHG", help=None),
                
                bepolyelectrolyte  = dict(id=20, cl=BEPolyelectrolyte, cat=_SHAPE_INDEP, name="BEPolyelectrolyte", help=None),
                dab                = dict(id=21, cl=DABModel,          cat=_SHAPE_INDEP, name="DAB", help=None),
                guiner             = dict(id=22, cl=GuinierModel,      cat=_SHAPE_INDEP, name="Guiner", help=None),
                debye              = dict(id=23, cl=DebyeModel,        cat=_SHAPE_INDEP, name="Debye", help=None),
                porod              = dict(id=24, cl=PorodModel,        cat=_SHAPE_INDEP, name="Porod", help=None),
                gausian            = dict(id=25, cl=PeakGaussModel,    cat=_SHAPE_INDEP, name="Gaussian Peak", help=None),
                lorentzpeak        = dict(id=26, cl=PeakLorentzModel,  cat=_SHAPE_INDEP, name="Lorentz Peak", help=None),
                fractal            = dict(id=27, cl=FractalAbsModel,   cat=_SHAPE_INDEP, name="Fractal", help=None),
                lorentz            = dict(id=28, cl=LorentzModel,      cat=_SHAPE_INDEP, name="Lorentz", help=None),
                powerlaw           = dict(id=29, cl=PowerLawAbsModel,  cat=_SHAPE_INDEP, name="Power Law", help=None),
                teubnerstrey       = dict(id=30, cl=TeubnerStreyModel, cat=_SHAPE_INDEP, name="Teubner-Strey", help=None),
                linear             = dict(id=31, cl=LineModel,         cat=_SHAPE_INDEP, name="Linear", help=None)
                )
                

def get_empty_parameter_dict():
    """
        Returns an empty parameter dictionary
    """
    return dict(short_name = '',
                long_name  = '',
                value      = 0,
                help       = '',
                error      = None,
                units      = '',
                checked    = False)

def get_model_list():
    return copy.deepcopy(_models)
    
def get_model_name_by_id(model_id):
    models = [item['name'] for item in _models.values() if item['id']==model_id]
    return models[0]

def get_model(model_id):
    """
        Returns the model class associated with a unique ID number
        
        @param model_id: ID of the model [integer]
        @return: sans.model class 
    """
    # Make sure we have an integer
    model_id = int(model_id)
    
    # Method that will identify the right model
    def _id_model(model):
        if _models[model]['id']==model_id:
            return True
        return False    

    # There should be only one model in the list
    model_list = filter(_id_model, _models)
    if len(model_list) == 0:
        raise ValueError, "sans_model_adapter.get_model: no model with ID=%d" % model_id
    if len(model_list) != 1:
        raise RuntimeError, "sans_model_adapter.get_model: ID=%d is not unique" % model_id
    
    return _models[model_list[0]]['cl']

def get_models_as_list():
    """
        Returns a list of models as a list of [ID, name]
    """
    model_list = []
    for item in _models:
        model_list.append([_models[item]['id'], _models[item]['name']])
    return model_list

def get_model_parameters(model_id, user_values=None, errors=None):
    """
        Returns a list of parameters for the specified model
        TODO: the values and errors should be filled by FitProblem.
        Only default values belong here.
        Should consider making this method part of FitProblem.
    """
    
    params = []
    m = get_model(model_id)()
    for item in m.params:
        if item not in m.orientation_params:
            units = m.details[item][0]
            
            # A little prettyfying
            units = units.replace('[A', '[&#197;')
            units = units.replace('[1/A', '[1/&#197;')
            units = units.replace('^(2)', "<span class='exponent'>2</span>")
            
            value = m.params[item]
            if type(user_values) == dict and user_values.has_key(item):
                value = user_values[item]
                
            error = None
            checked = False
            if type(errors) == dict and errors.has_key(item):
                error = "%-5.2g" % errors[item]
                checked = True
            
            params.append(dict(short_name=item,
                                long_name="%s %s" % (item, units),
                                units=units,
                                value=value,
                                help='',
                                error=error,
                                checked=checked))
            
    return params

def _get_errors(data_info):
    if len(data_info.x) != len(data_info.y):
        raise RuntimeError, "sans_model_adapter.compute_model: x and y have different lengths"
    dy = data_info.dy
    if data_info.dy is None or len(data_info.dy) != len(data_info.x):
        dy = numpy.ones(len(data_info.x))    
    return dy
    

def compute_model(fit_problem, iq_id, data_info):
    """
    
    """
    # Construct SANS model object
    model = model_from_fit_problem(fit_problem)
    
    # Get Q range
    if fit_problem.qmin is not None: qmin = fit_problem.qmin
    else: qmin = min(data_info.x)
    
    if fit_problem.qmax is not None: qmax = fit_problem.qmax
    else: qmax = max(data_info.x)

    # Error bars, for chi2 computation
    dy = _get_errors(data_info)
    
    # Smearing 
    smearer = fit_problem.get_smearer(data_info)
    
    f = SansFit(model, data_info, smearer=smearer, qmin=qmin, qmax=qmax) 
    xdist, iq_calc = f.get_model_distribution()
    chi2 = f.chi2()
    
    return {'iq_id':iq_id,
            'x':xdist,
            'y':iq_calc,
            'dy':None,
            'chi2':chi2,
            'errors':[]}
    
def perform_fit(fit_problem, iq_id, data_info):
    """
    """
    # Construct SANS model object
    model = model_from_fit_problem(fit_problem)
    
    # Get Q range
    if fit_problem.qmin is not None: qmin = fit_problem.qmin
    else: qmin = min(data_info.x)
    
    if fit_problem.qmax is not None: qmax = fit_problem.qmax
    else: qmax = max(data_info.x)

    # Find what parameter are flagged for fitting
    fitting_params = []
    for i in range(len(fit_problem.model_parameters)):
        p = fit_problem.model_parameters[i]
        if p.has_key('checked') and p['checked'] is not None and p['checked']:
            fitting_params.append(Parameter(model, p['short_name'], p['value'], id=i))

    dy = _get_errors(data_info)  
    
    # Smearing 
    smearer = fit_problem.get_smearer(data_info)
    
    f = SansFit(model, data_info, fitting_params, smearer=smearer, qmin=qmin, qmax=qmax) 
    out, cov = f.fit()
    chisqr = f.chi2()
    
    # The output of optimize.leastsquare is a list only if the number of
    # fit parameters is greater than 1.
    if len(fitting_params)==1:
        out = [out]
        
    for i in range(len(fitting_params)):
        fit_problem.model_parameters[fitting_params[i].id]['value'] = out[i]
        try:
            fit_problem.model_parameters[fitting_params[i].id]['error'] = math.sqrt(cov[i][i])
        except:
            fit_problem.model_parameters[fitting_params[i].id]['error'] = out[i]

    # Store chi2
    fit_problem.chi2 = chisqr
    return chisqr

def model_from_fit_problem(fit_problem):
    """
        Constructs a SANS model from a fit problem
        
        @param fit_problem: FitProblem object
        @return: sansmodels model object.
    """
    model = get_model(fit_problem.model_id)()
    
    # Populate parameters with fit problem values
    for p in fit_problem.model_parameters:
        if model.params.has_key(p['short_name']):
            model.setParam(p['short_name'], p['value'])
    
    return model

class FitProblem(object):
    ## Model ID
    model_id = 0
    ## Model name
    model_name = None
    ## Data ID
    data_id  = None
    ## Minimum Q
    qmin = None
    ## Maximum Q
    qmax = None
    ## Smearing model ID
    smearer_model_id = None
    ## Smearing option [tells us whether the model was chosen by the user or not]
    smearer_option_id = 0
    ## Smearing adapter
    smear_adapter = None
    
    ## Model parameters
    model_parameters = []
    
    ## Output Chi2
    chi2 = None
    
    ## Flag set to true if the object was created from a valid form
    is_valid = False
    
    def __init__(self, qmin=None, qmax=None, model_id=0, data_id=None):
        """
            A model ID can be specified if 'parameters' is incomplete or None.
            If 'parameters' contains model information, it will supersede 'model_id'.
            
            @param qmin: Minimum Q-value for the model
            @param qmax: Maximum Q-value for the model
            @param parameters: clean form parameters
            @param model_id: Model ID
        """
        self.model_id = model_id
        self.data_id = data_id
        self.qmin = qmin
        self.qmax = qmax
        self.model_name = get_model_name_by_id(model_id)
    
    def __str__(self):
        str = "Model ID: %s (%s)\n" % (self.model_id, self.model_name)
        for p in self.model_parameters:
            checked = '*' if p['checked'] else ''
            str += "  %s%s = %s +- %s\n" % (p['short_name'], checked, p['value'], p['error'])
        str += "\nQ min = %s  Q max = %s\n" %(self.qmin, self.qmax)
        str += "Smearing: %s [Option: %s]\n" % (self.smearer_model_id, self.smearer_option_id)
        if self.smear_adapter is not None:
            str += "  is_fixed = %s" % self.smear_adapter.is_fixed 
            for p in self.smear_adapter.get_smearing_parameters():
                str += "  %s = %s" % (p['short_name'], p['value'])
        
        return str
    
    def fit_parameter_selected(self):
        """
            Returns True if a parameter was selected for fitting
        """
        for p in self.model_parameters:
            if p.has_key('checked') and p['checked']:
                return True
        return False   
        
    def process_model_parameter_list(self, model_parameters=None): 
        """
            Processes a list of parameters, where each parameter is a dictionary
            in the format of what is stored under model_parameters.
        """
        # Set the parameter values
        self.model_parameters = get_model_parameters(self.model_id)
        for p in model_parameters:
            for _p in self.model_parameters:
                if p['short_name'] == _p['short_name']:
                    _p['value']   = p['value']
                    _p['checked'] = p['checked']
                    _p['error']   = p['error']

    def get_smearer(self, data1d):
        """
            Returns a smearer object for the given Data1D object
        """
        if self.smearer_option_id==smearing_model_adapter.DEFAULT_SMEARING_ID:
            return smearing_model_adapter.get_default_smearer(data1d)
        elif self.smear_adapter is not None:
            return self.smear_adapter.get_smearer(data1d)
            
        return None
        
    def get_formatted_model_parameters(self):
        pars = copy.deepcopy(self.model_parameters)
        for p in pars:
           exec "p['value'] = '%-5.3g' % p['value']"
           if p['error'] is not None:
               exec "p['error'] = '%-5.2g' % p['error']"
        return pars
        
    def get_model_parameters_as_list(self):
        """
            Returns a list of the names of the model parameters
        """
        params = []
        for item in self.model_parameters:
            params.append(item['short_name'])
        return params       
        
    