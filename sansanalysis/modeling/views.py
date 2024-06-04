import sys, math

# Django imports
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.template import Context, loader

# Application dependency imports
import sansanalysis.settings
from sansanalysis.simpleplot.views import confirm_access, _process_plot_scale, _data_template_args, _common_template_args
from sansanalysis.simpleplot import view_util
from sansanalysis.app_logging.models import store_error
from sansanalysis.simpleplot.models import IqData
from sansanalysis.simpleplot.manipulations import iqdata as iq_data_manipulations

# Application imports
import forms as modeling_forms
from sansanalysis.modeling.models import FitProblem
from sansanalysis.modeling.forms import ModelForm, model_parameters_as_xml, model_parameters_as_list, model_parameters_as_table
import view_util as modeling_view_util
#from sansanalysis.modeling import manipulations
import sansanalysis.modeling.sans_model_adapter as sans_model_adapter
import sansanalysis.modeling.data_manipulations as data_manipulations
import sansanalysis.modeling.smearing_model_adapter as smearing_model_adapter

#TODO: refactor all the imports from simpleplot.views
#TODO: check for Q=0, skip those points and notify user

@login_required
@confirm_access
def fit(request, iq_id=0, fit_id=None):
    """
TODO: calls to share modeling fits, unit tests for shared fits
TODO: test what happens when a non-registered user hits the shared link [OK]
TODO: store shared fit / delete shared fit [DONE]
TODO: Update dashboard [DONE]
TODO: Data summary page should be a mini dashboard for that data set
TODO: pick model from a list of old fits
TODO: add more models [DONE]
TODO: polydisp
TODO: reload doesn't work (need some js to select the right control options - radio buttons)
TODO: structure factor
TODO: when no smearing info is available, make sure that the message "no smearinf info" is shown after the fit when Data Default is selected        
TODO: need to divide Chi2 by DoF
    """   
    # Check that a data set is available
    iq = get_object_or_404(IqData, pk=iq_id)
    
    if fit_id is not None:
        # IDs should be integers
        try:
            fit_id = int(fit_id)
        except:
            raise Http404
        
        # Check that the fit exists
        fit = get_object_or_404(FitProblem, pk=fit_id)
    
    # Process GET arguments for plot scale
    #TODO: put this in a decorator
    _process_plot_scale(request)
    
    # Get plot data
    try:
        iq_data, ticks_x, ticks_y, errors = view_util.get_plottable_iq(request, iq)              
    except:
        # Send user to error page
        error_msg = 'fit() could not process stored data\n%s' % sys.exc_value
        err_id = store_error(user=request.user, url=request.path, text=error_msg, method='modeling.views.fit', is_shown=True, build=sansanalysis.settings.APP_VERSION)
        return render_to_response('simpleplot/error.html',
                                  {'error': 'Error ID = %s: Could not process stored data' % str(err_id)},
                                  context_instance=RequestContext(request))


    # If we got a fit ID, use that information
    # Otherwise get last model from the session if available
    if fit_id is not None:
        fit_problem = data_manipulations.restore_fit_problem(fit_id)
    else:
        model_params = {}
        if request.session.get('sans_fit_iqid', default=None) == iq_id:
            model_params = request.session.get('sans_model_params', default={})
        # Specify q range if not available
        qmin, qmax = view_util.get_qrange_iq(request, iq)
        fit_problem  = sans_model_adapter.FitProblem(qmin=qmin, qmax=qmax, data_id=iq_id)
        modeling_forms.populate_fit_problem_from_form_data(fit_problem, model_params)
    
    # Info to be displayed to the user
    chisqr = None
    messages = []
    
    # Process the POST data if applicable
    if request.method == 'POST':
        form = modeling_forms.populate_fit_problem_from_query_data(request.POST, fit_problem)
        
        if fit_problem.is_valid:
            if fit_problem.fit_parameter_selected():
                try:
                    chisqr = data_manipulations.perform_fit(fit_problem, iq_id)
                    # Store the fit problem and its results
                    stored_fp = data_manipulations.store_fit_problem(request.user, fit_problem)

                    # Keep the new parameters as session data
                    request.session['sans_model_params'] = modeling_forms.fit_problem_as_form_data(fit_problem)
                    request.session['sans_fit_iqid'] = iq_id
                    return HttpResponseRedirect(reverse('sansanalysis.modeling.views.fit', args=(iq_id, stored_fp.id,)))   
                except:
                    error_msg = "fit() could not fit data:\n%s" % sys.exc_value
                    err_id = store_error(user=request.user, url=request.path, text=error_msg, method='modeling.views.fit', is_shown=True, build=sansanalysis.settings.APP_VERSION)
                    return render_to_response('simpleplot/error.html',
                                              {'error': "Error ID = %s: Could not fit your data" % str(iq_id)},
                                              context_instance=RequestContext(request))
            else:
                messages.append("Please check at least one parameter.")
        
    else:
        form = modeling_forms.fit_problem_as_form(fit_problem)
        
    iq_dist = data_manipulations.compute_model(fit_problem, iq_id)
    
    try:
        chisqr = "%-5.2g" % iq_dist['chi2']
    except:
        chisqr = "Not available"
        
    scale_x = request.session.get(view_util.DATA_SCALE_X_QSTRING, default='linear')
    scale_y = request.session.get(view_util.DATA_SCALE_Y_QSTRING, default='linear')
    iq_calc, iq_ticks_x, iq_ticks_y = view_util.get_plot_data(iq_dist, scale_x, scale_y)  
        
    # Action list
    actions = []
    if fit_id is not None:
        if request.user.id == iq.owner :  
            actions.append({'name': 'Share this modeling fit',
                            'attrs': [{'name'  : 'onClick',
                                      'value' : "\"get_fit_shared_key('%s', %s, %s);\"" % (iq.name, iq.id, fit_id)},
                                      {'name' : 'title',
                                       'value': "\"Click to generate a link that you can send other people you want to share this fit with.\""}]})
    
        # Check whether the user has the data in his shared list
        elif data_manipulations.has_shared_fit(request.user, fit):
            pass
        
        elif modeling_view_util.get_shared_fit_key_from_session(request, fit_id) is not None:
            fit_key = modeling_view_util.get_shared_fit_key_from_session(request, fit_id)
            actions.append({'name': 'Store this modeling fit',
                            'url': reverse('sansanalysis.modeling.views.store_fit', args=(fit_key,)),
                            'attrs': [{'name' : 'title',
                                       'value': "\"Click to keep this data set in your permanent list of shared data. By doing so, you will no longer need to use the link provided to you to access the data.\""}]})


    breadcrumbs = "<a href='%s'>Home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; Model fitting" % (reverse('sansanalysis.simpleplot.views.home'),
                                                      reverse('sansanalysis.simpleplot.views.data_details', args=(iq_id,)), iq.name) 
    
    # Prepare the response
    template_args = {  'iq_data':str(iq_data),
                       'form': form,
                       'ticks_x': ticks_x,
                       'ticks_y': ticks_y,
                       'iq_id': iq_id,
                       'iq_calc': str(iq_calc),
                       'iq_name':iq.name,
                       'actions': actions,
                       'chisqr': chisqr,
                       'breadcrumbs': breadcrumbs,
                       'user_alert': messages}
    template_args = _data_template_args(request, iq, **template_args)
    template_args = modeling_view_util.fit_problem_template_args(fit_problem, **template_args)
    
    return render_to_response('modeling/fit.html', 
                              template_args,
                               context_instance=RequestContext(request))
    
@login_required
def get_model_table(request, model_id):
    """
        Ajax call to get the information to populate a model input form.
        When we get this call, it's because the user is changing models, 
        so the parameters should be populated with default values, unless
        we are getting a model from a past fit.
        
        @param model_id: the ID of the model to be used 
    """
    if request.session.get('sans_model_id', default=None) == model_id: 
        last_model_params = request.session.get('sans_model_params', default=None)
    else:
        last_model_params = None

    try:
        resp = model_parameters_as_table(model_id, last_model_params)
    except:
        error_msg = "modeling.get_model_table: could not get model parameters\n%s" % sys.exc_value
        err_id = store_error(user=request.user, url=request.path, text=error_msg, method='modeling.views.get_model_table', is_shown=False, build=sansanalysis.settings.APP_VERSION)
        resp = ''
    return HttpResponse(resp, mimetype="text/html")

@login_required
def get_model_parameters(request, model_id):
    """
        Ajax call to get the information to populate a model input form.
        When we get this call, it's because the user is changing models, 
        so the parameters should be populated with default values, unless
        we are getting a model from a past fit.
        
        @param model_id: the ID of the model to be used 
    """
    # Verify that the model ID is an int
    try:
        model_id = int(model_id)
    except:
        raise Http404
    try:
        parlist = model_parameters_as_xml(model_id)
    except:
        error_msg = "modeling.get_model_parameters: could not get model parameters\n%s" % sys.exc_value
        err_id = store_error(user=request.user, url=request.path, text=error_msg, method='modeling.views.get_model_parameters', is_shown=True, build=sansanalysis.settings.APP_VERSION)
        resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<error>Error %s: The system could not get your model parameters. We're on it!</error>\n" % err_id
        return HttpResponse(resp, mimetype="text/xml")

    resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<parlist>%s</parlist>\n" % parlist
    return HttpResponse(resp, mimetype="text/xml")

@login_required
def get_smearing_parameters(request, model_id):
    """
        Ajax call to get the information to populate a smearing model input form.
        When we get this call, it's because the user is changing models, 
        so the parameters should be populated with default values, unless
        we are getting a model from a past fit.
        
        @param model_id: the ID of the model to be used 
    """
    
    # Verify that the model ID is an int
    try:
        model_id = int(model_id)
    except:
        raise Http404
    
    is_fixed = request.GET.get('fixed', default='false')=='true'
    model_id = smearing_model_adapter.get_smearing_model_id_by_name(request.GET.get('id', default=None))
    
    try:
        parlist = modeling_forms.smearing_parameters_as_xml(model_id, is_fixed)
    except:
        error_msg = "modeling.get_smearing_parameters: could not get model parameters\n%s" % sys.exc_value
        err_id = store_error(user=request.user, url=request.path, text=error_msg, method='modeling.views.get_smearing_parameters', is_shown=True, build=sansanalysis.settings.APP_VERSION)
        resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<error>Error %s: The system could not get your model parameters. We're on it!</error>\n" % err_id
        return HttpResponse(resp, mimetype="text/xml")

    resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<parlist>%s</parlist>\n" % parlist
    return HttpResponse(resp, mimetype="text/xml")

@login_required
@confirm_access
def get_model_update(request, iq_id, model_id):
    """
        Ajax call to evaluate a model at the Q points of the last shown data set.
        Parameters are sent with the call, along with the data PK for checking.
    """
    # Check that a data set is available
    iq = get_object_or_404(IqData, pk=iq_id)
    
    # Process GET arguments for plot scale
    _process_plot_scale(request)
    
    try:        
        fit_problem  = sans_model_adapter.FitProblem()
        form = modeling_forms.populate_fit_problem_from_query_data(request.GET, fit_problem)
                
        if fit_problem.is_valid:
            # If the parameters are valid, update the model
            iq_dist = data_manipulations.compute_model(fit_problem, iq_id)
            scale_x = request.session.get(view_util.DATA_SCALE_X_QSTRING, default='linear')
            scale_y = request.session.get(view_util.DATA_SCALE_Y_QSTRING, default='linear')
            iq_calc, iq_ticks_x, iq_ticks_y = view_util.get_plot_data(iq_dist, scale_x, scale_y)  
            
            # Store the current parameters in the session  
            request.session['sans_model_params'] = modeling_forms.fit_problem_as_form_data(fit_problem)
            
            resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<distrib>\n"
            for i in range(len(iq_calc)):
                resp += "<point><x>%g</x><y>%g</y></point>\n" % (iq_calc[i][0], iq_calc[i][1])
            resp += "</distrib>"
            return HttpResponse(resp, mimetype="text/xml")
            
        else:
            errs = ""
            for item in form.errors:
                errs += "<error><par>%s</par><value>%s</value></error>" % (item, form.errors[item])
                
            resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<distrib>%s</distrib>\n" % errs
            return HttpResponse(resp, mimetype="text/xml")
    
    except:
        err_mess = "get_model_update failed: %s" % sys.exc_value
        err_id = store_error(user=request.user, url=request.path, text=err_mess, method='modeling.views.get_model_update', build=sansanalysis.settings.APP_VERSION)
        resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<error><par>Server Error</par><value>Error %s: The system could not compute your model. We're on it!</value></error>\n" % err_id
        return HttpResponse(resp, mimetype="text/xml")
   
   
    resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<distrib></distrib>" 
    return HttpResponse(resp, mimetype="text/xml")


@login_required
@confirm_access
def get_smearing_table(request, iq_id):
    """
        Ajax call to get the information to populate a smearing input form.
        When we get this call, it's because the user is changing models, 
        so the parameters should be populated with default values, unless
        we are getting a model from a past fit.
        
        @param iq_id: the ID of the data set under consideration
    """
    # Check whether we want the default, or a custom table.
    type = request.GET.get('type', default=None)
    type_id = None
    if type=='point':
        type_id = smearing_model_adapter.POINT_SMEARING_ID
    elif type=='slit':
        type_id = smearing_model_adapter.SLIT_SMEARING_ID
        
    try:
        resp = modeling_view_util.smearing_model_as_table(request, type_id, iq_id)
    except:
        error_msg = "modeling.get_smearing_table: could not get smearing parameters\n%s" % sys.exc_value
        err_id = store_error(user=request.user, url=request.path, text=error_msg, method='modeling.views.get_smearing_table', is_shown=False, build=sansanalysis.settings.APP_VERSION)
        resp = ''
    return HttpResponse(resp, mimetype="text/html")


@login_required
def share_fit(request, iq_id, fit_id):
    """
        Ajax call
    """

    # Get data information
    iq = get_object_or_404(IqData, pk=iq_id)
    fit = FitProblem.objects.get(owner__id=request.user.id, iq_data__id=iq_id, pk=fit_id)

    # Check whether a key exists for this data
    key = data_manipulations.get_fit_shared_key(fit, create=True)
        
    permalink = reverse('sansanalysis.modeling.views.access_shared_fit', args=(key,))
    permalink = sansanalysis.settings.APP_DOMAIN+permalink
    
    resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<key>%s</key>" % permalink
    return HttpResponse(resp, mimetype="text/xml")


@login_required
def delete_fit(request, iq_id, fit_id):
    """
        Delete a FitProblem entry
        TODO: don't hardcode the dashboard location
    """
    fit = get_object_or_404(FitProblem, pk=fit_id)

    # Check whether the user is the owner of the fit
    if request.user.id == fit.owner.id:
        # Deactivate the fit for this user / shared links will be kept
        data_manipulations.deactivate_fit(fit)
    
    # Check whether the user has the data in his shared list
    elif data_manipulations.has_shared_fit(request.user, fit):
        # Delete the link between this user and the data set
        data_manipulations.remove_shared_link(fit, request.user)
    
    return view_util.dashboard_response()


def access_shared_fit(request, key):
    """
    """
    # Find the key and its associated data set
    fit = data_manipulations.get_anonymous_shared_fit(key)
    if fit is None:
        raise Http404
    
    # Store key in session
    request.session['fit_shared_key'] = {}
    request.session['fit_shared_key'][fit.id] = key
    
    # Store data key in session, to let the user access the data
    data_key = iq_data_manipulations.get_data_shared_key(fit.iq_data, create=True)
    request.session['data_shared_key'] = {}
    request.session['data_shared_key'][fit.iq_data.id] = data_key
    
    # Check whether the user is authenticated, if not redirect them to the data page.
    
    if not request.user.is_authenticated():
        # Check whether a key exists for this data
        permalink = reverse('sansanalysis.simpleplot.views.access_shared_data', args=(data_key,))
        permalink = sansanalysis.settings.APP_DOMAIN+permalink 
        
        welcome = "\"The computational functionality on this site is only available to registered users.<p>"
        welcome += "Please follow the instructions on this page to register in order to view the I(q) modeling fit you are trying to access.<p>"
        welcome += "Alternatively, you can follow the link below to view the data:<p>"
        welcome += "<a href='%s'>%s</a>\"" % (permalink, fit.iq_data.name)

        template_args = {'popup_alert': welcome}
        template_args = _common_template_args(request, **template_args)
        return render_to_response('simpleplot/index.html', 
                           template_args,
                           context_instance=RequestContext(request))
    
    return HttpResponseRedirect(reverse('sansanalysis.modeling.views.fit', args=(fit.iq_data.id, fit.id,)))    

  
@login_required    
def store_fit(request, key):
    """
        Store the link to the FitProblem object corresponding to the given key
    """
    # Find the key and its associated data set
    fit = data_manipulations.get_anonymous_shared_fit(key)
    if fit is None:
        raise Http404
    
    # Verify that the link doesn't already exist
    data_manipulations.create_shared_link(request.user, fit)
    
    # Create a link to the data as well
    iq_data_manipulations.create_shared_link(request.user, fit.iq_data)
    
    return HttpResponseRedirect(reverse('sansanalysis.modeling.views.fit', args=(fit.iq_data.id, fit.id)))    


@login_required
def get_fit_model_dialog(request):
    """
        Ajax call to get the model panel.
    """
    t = loader.get_template('modeling/fit_model_dialog.html')

    # Model list
    model_list = sans_model_adapter.get_model_list()

    c = Context({
            'models': model_list.values(),
        })
    resp = t.render(c)
    return HttpResponse(resp, mimetype="text/html")


