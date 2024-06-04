# Django imports
from django.template import Context, loader

# Application imports
import smearing_model_adapter
import data_manipulations
import forms as modeling_forms
 
def fit_problem_template_args(fit_problem, **template_args):
    """
    """
    template_args['params'] = fit_problem.get_formatted_model_parameters()
    template_args['model_id'] = fit_problem.model_id
    template_args['model_name'] = fit_problem.model_name.capitalize()
    template_args['model_params_list'] = str(fit_problem.get_model_parameters_as_list())
    template_args['smearing'] = fit_problem.smearer_option_id
    
    # Get smearing parameters as appropriate
    smear_type = fit_problem.smearer_model_id
    fixed = not (fit_problem.smearer_option_id in [smearing_model_adapter.POINT_SMEARING_ID, 
                                         smearing_model_adapter.SLIT_SMEARING_ID])

    if fit_problem.smear_adapter is not None:
        params = fit_problem.smear_adapter.get_smearing_parameters()
        params_list = fit_problem.smear_adapter.get_smearing_parameters_as_list()
        template_args['smear_type'] = smear_type
        template_args['smear_type_id'] = fit_problem.smear_adapter.id
        template_args['smear_fixed'] = fixed
        template_args['smear_params'] = params
        template_args['smear_params_list'] = str(params_list)

    return template_args

def smearing_model_as_table(request, smearer_model_id=None, iq_id=None):
    """
        Returns an HTML table with the parameters of a smearing model
        @param iq_id: ID of IqData object
        @param custom: if True, a form will be returned instead of a table of constants
    """
    t = loader.get_template('modeling/smearing_parameters.html')

    # Get the data object if available
    if iq_id is not None:
        data1d = data_manipulations.get_data(iq_id)

    # Defaults
    # TODO: This needs to be a short string to be compatible 
    # with the max length of the smearing type in the DB.
    # We should definitely fix this.
    type = "No smearing info"
    params = []
    fixed = True

    adapter = None    
    adapter_cls = smearing_model_adapter.get_smear_adapter_class_by_type(smearer_model_id)
    
    if smearer_model_id is not None:
        adapter_cls = smearing_model_adapter.get_smear_adapter_class_by_type(smearer_model_id)
        if adapter_cls is not None:
            adapter = adapter_cls()
    elif iq_id is not None:
        adapter = smearing_model_adapter.get_default_smear_adapter(data1d)
    else:
        raise ValueError, "view_util.smearing_model_as_table takes either a model ID or a Data1D object"
    
    if adapter is not None:
        type = adapter.name
        params = adapter.get_formatted_smearing_parameters()
        fixed = adapter.is_fixed
        
        # Update session data
        if request.session.get('sans_model_params', default=None) is None:
            request.session['sans_model_params'] = {}
        request.session['sans_model_params'].update(modeling_forms.smear_adapter_as_form_data(adapter))

    c = Context({
            'smear_params': params,
            'smear_fixed': fixed,
            'smear_type': type,
        })
    return t.render(c)
        

def get_shared_fit_key_from_session(request, fit_id):
    """
        Checks whether the user has the correct shared key for a given fit stored in the session,
        if so return the key.
        
        @param fit_id: PK of FitProblem object
    """
    if (request.session.get('fit_shared_key', default=None) != None \
        and request.session.get('fit_shared_key').has_key(fit_id) \
        and request.session.get('fit_shared_key')[fit_id] == data_manipulations.get_fit_shared_key(fit_id)):
        return request.session.get('fit_shared_key')[fit_id]
    return None

        