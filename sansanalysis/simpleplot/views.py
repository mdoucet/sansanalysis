from django.shortcuts import get_object_or_404, render_to_response
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.files.base import ContentFile
from django import forms
from django.contrib.auth.decorators import login_required

from django.template import RequestContext
import urllib2

from sansanalysis.simpleplot.forms.prforms import PrForm
from sansanalysis.simpleplot.forms.iqforms import ShareForm
import sansanalysis.settings
import sansanalysis.common.view_util as common_view_util

import view_util


from django.contrib.auth.models import User
from sansanalysis.simpleplot.models import IqData, RecentData, PrInversion, UserSharedData
from sansanalysis.app_logging.models import store_error
import math, os, sys, traceback

# Data manipulations
import manipulations.iqdata
import manipulations.prdata

def confirm_access(view):
    """
        Method decorator to check whether the requested data exists
        and is accessible to the user requesting it. 
    """
    def validated_view(request, iq_id, *args, **kws):
        # IDs should be integers
        try:
            iq_id = int(iq_id)
        except:
            raise Http404
        # Verify that the requested data exists 
        iq = get_object_or_404(IqData, pk=iq_id)
        # Check that the current user owns the data
        if request.user.id == iq.owner \
            or (request.user.is_authenticated() and manipulations.iqdata.has_shared_data(request.user, iq)) \
            or (request.session.get('data_shared_key', default=None) != None \
                and request.session.get('data_shared_key').has_key(iq.id) \
                and request.session.get('data_shared_key')[iq.id] == manipulations.iqdata.get_data_shared_key(iq.id)):
            
            return view(request, iq_id, *args, **kws)
        else:
            error_msg = "User does not have access to data"
            err_id = store_error(user=request.user, url=request.path, text=error_msg, method='simpleplot.views.confirm_access', is_shown=True, build=sansanalysis.settings.APP_VERSION)
            return render_to_response('simpleplot/error.html',
                                      {'error': 'Error ID = %s: Access denied' % str(err_id)}, 
                                      context_instance=RequestContext(request))
        
    return validated_view    


@login_required
@confirm_access
def invert(request, iq_id, pr_id=None):
    
    # Perform some sanity checks if we are trying to access a specific fit
    if pr_id is not None:
        # IDs should be integers
        try:
            pr_id = int(pr_id)
        except:
            raise Http404
        
        # Check whether we have a shared key for that fit
        pr_key = view_util.get_shared_pr_key(request, pr_id)
        
        # Check that the inversion exists
        pr = get_object_or_404(PrInversion, pk=pr_id)

    
    # Check that a data set is available
    iq = get_object_or_404(IqData, pk=iq_id)
    
    # Process GET arguments for plot scale
    _process_plot_scale(request)
    
    try:
        iq_data, ticks_x, ticks_y, errors = view_util.get_plottable_iq(request, iq)        
    except:
        # Send user to error page
        error_msg = 'invert() could not process stored data\n%s' % sys.exc_value
        err_id = store_error(user=request.user, url=request.path, text=error_msg, method='simpleplot.views.invert', is_shown=True, build=sansanalysis.settings.APP_VERSION)
        return render_to_response('simpleplot/error.html',
                                  {'error': 'Error ID = %s: Could not process stored data' % str(err_id)},
                                  context_instance=RequestContext(request))
    
    iq_dist = None
    pr_dist = None
    pr_outputs = None
    messages = []
    
    # Fill out the form 
    if request.method == 'POST': # If the form has been submitted...
        form = PrForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Provide and error box for computation-related errors.
            try:
                invertor = manipulations.prdata.PrInvertor()
                iq_dist, pr_dist, pr_id = invertor(iq_id, form.cleaned_data, request.user.id) 
                      
                request.session['pr_params'] = form.cleaned_data
            except:
                error_msg = "invert() could not compute P(r)\n%s" % sys.exc_value
                err_id = store_error(user=request.user, url=request.path, text=error_msg, method='simpleplot.views.invert', is_shown=True, build=sansanalysis.settings.APP_VERSION)
                return render_to_response('simpleplot/error.html',
                                          {'error': "Error ID = %s: Could not compute P(r)" % str(err_id)},
                                          context_instance=RequestContext(request))
                
            return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.invert', args=(iq_id,
                                                                                          pr_id,)))              
    else:
        # Fill the form with the last computed P(r)
        prfit = None
        if pr_id is not None:
            _prfit = manipulations.prdata.get_pr(pr_id, user_id=request.user.id, iq_id=iq_id, key=pr_key)
            if _prfit is not None:
                prfit = [_prfit]
        else:
            prfit = PrInversion.objects.filter(user_id=request.user.id, iq_data__id=iq_id).order_by('created_on').reverse()
        
        if prfit is not None and len(prfit)>0:
            try:
                invertor = manipulations.prdata.PrInvertor()
                # Get the pk of the PrOutput associated with this fit, if available
                pr_output_id = manipulations.prdata.get_pr_output_id(prfit[0].id)
                if pr_output_id is not None:
                    iq_dist = invertor.get_iq_calc(pr_output_id)
                    pr_dist = invertor.get_pr(pr_output_id)
                    pr_params = prfit[0].get_parameters()
                    pr_outputs = invertor.get_outputs(pr_output_id)
                    # Get the user alerts
                    if len(invertor.messages)>0:
                        messages = invertor.messages
                else:
                    messages = ["Warning: No output parameters could be retrieved for this fit. The inversion may not have completed properly."]
            except:
                error_msg = "invert() could not retrieve P(r)\n%s" % sys.exc_value
                err_id = store_error(user=request.user, url=request.path, text=error_msg, method='simpleplot.views.invert', is_shown=True, build=sansanalysis.settings.APP_VERSION)                
                return render_to_response('simpleplot/error.html',
                                          {'error': "Error ID = %s: Could not compute P(r)" % str(err_id)},
                                          context_instance=RequestContext(request))                    
        else:
            pr_params = request.session.get('pr_params', default=None)
            if pr_params is None:
                pr_params={'d_max': '150.0',
                           'n_terms': '12',
                           'alpha': '0'}
        form = PrForm(initial=pr_params) # An unbound form
        
    # Latest computed I(Q)
    scale_x = request.session.get(view_util.DATA_SCALE_X_QSTRING, default='linear')
    scale_y = request.session.get(view_util.DATA_SCALE_Y_QSTRING, default='linear')
    outscale_x = request.session.get(view_util.OUTPUT_SCALE_X_QSTRING, default='linear')
    outscale_y = request.session.get(view_util.OUTPUT_SCALE_Y_QSTRING, default='linear')
    
    iq_calc, iq_ticks_x, iq_ticks_y = view_util.get_plot_data(iq_dist, scale_x, scale_y)    
    pr_calc, pr_ticks_x, pr_ticks_y = view_util.get_plot_data(pr_dist, outscale_x, outscale_y)    
    
    iq_calc_str = str(iq_calc) if len(iq_calc)>0 else None
    pr_calc_str = str(pr_calc) if len(pr_calc)>0 else None
    
    # Action list
    actions = []
    
    if request.user.is_authenticated() and pr_id is not None:
        if request.user.id == iq.owner :  
            actions.append({'name': 'Share this P(r) fit',
                            'attrs': [{'name'  : 'onClick',
                                      'value' : "\"get_pr_shared_key($, '%s', %s, %s);\"" % (iq.name, iq.id, pr_id)},
                                      {'name' : 'title',
                                       'value': "\"Click to generate a link that you can send other people you want to share this fit with.\""}]})
        # Check whether the user has the data in his shared list
        elif manipulations.prdata.has_shared_pr(request.user, pr):
            pass
        
        elif view_util.get_shared_pr_key(request, pr_id) is not None:
            actions.append({'name': 'Store this P(r) fit',
                            'url': reverse('sansanalysis.simpleplot.views.store_pr', args=(pr_key,)),
                            'attrs': [{'name' : 'title',
                                       'value': "\"Click to keep this data set in your permanent list of shared data. By doing so, you will no longer need to use the link provided to you to access the data.\""}]})

    breadcrumbs = "<a href='%s'>Home</a> &rsaquo; <a href='%s'>%s</a> &rsaquo; P(r) inversion" % (reverse('sansanalysis.simpleplot.views.home'),
                                                      reverse('sansanalysis.simpleplot.views.data_details', args=(iq_id,)), iq.name) 
    
    # Prepare the response
    template_args = {'iq_data':str(iq_data),
                       'form': form,
                       'ticks_x': ticks_x,
                       'ticks_y': ticks_y,
                       'iq_id': iq_id,
                       'iq_calc': iq_calc_str,
                       'iq_name':iq.name,
                       'output_data': pr_calc_str,
                       'output_xscale': outscale_x,
                       'output_yscale': outscale_y,
                       'output_ticks_x': pr_ticks_x,
                       'output_ticks_y': pr_ticks_y,
                       'pr_outputs': pr_outputs,
                       'actions': actions,
                       'breadcrumbs': breadcrumbs,
                       'user_alert': messages}
    template_args = _data_template_args(request, iq, **template_args)
    
    return render_to_response('simpleplot/invert.html', 
                              template_args,
                               context_instance=RequestContext(request))
    
class UploadFileForm(forms.Form):
    """
        Simple form to select a data file on the user's machine
    """
    # http://dl.dropbox.com/u/16900303/5731_frame1_Iq.xml
    file  = forms.FileField(required=False)
    data_url = forms.URLField(required=False, verify_exists=True)

@login_required
def select_data(request):
    """
        Dashboard page
    """
    # Get user data
    user_data, user_data_header, user_data_all_url = view_util.DataSorter(request)()    
    user_pr, user_pr_header, user_pr_all_url = view_util.BasePrSorter(request)()
    user_fit, user_fit_header, user_fit_all_url = view_util.ModelFitSorter(request)()
    
    # Upload form
    error_msg = None
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Prepare to save data to disk
            if 'file' in request.FILES:
                file_name = request.FILES['file'].name
                file_content = ContentFile(request.FILES['file'].read())
            else:
                data_url = request.POST['data_url']
                f = urllib2.urlopen(urllib2.Request(url=data_url))
                file_content = ContentFile(f.read())
                file_name = data_url
            # Search to see whether a file with that name exists.
            # Check whether the file is owned by the user before deleting it.
            # If it's not, just create a new file with the same name.
            iq_entries = IqData.objects.filter(name__endswith=file_name, owner=request.user.id)
            if len(iq_entries)>0:                
                iq_data = iq_entries[0]
                iq_data.file.delete(False)
            else:
                # No entry was found, create one
                iq_data = IqData()
                iq_data.owner = request.user.id
                iq_data.name  = file_name
            
            iq_data.file.save(file_name, file_content)
            
            return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.data_details', args=(iq_data.id,)))
        else:
            error_msg = "Enter a valid file path or a valid URL"
            if 'file' in request.FILES:
                file_name = request.FILES['file'].name
                error_msg += '<br><br> <i>%s</i> is invalid' % file_name
            if 'data_url' in request.POST:
                data_url = request.POST['data_url']
                error_msg += '<br><br> <i>%s</i> is invalid' % data_url
                
    else:
        form = UploadFileForm()
        
    # Template data
    breadcrumbs = "<a href='%s'>Home</a> &rsaquo; Dashboard" % (reverse('sansanalysis.simpleplot.views.home')) 
    
    template_args = {'form': form,
                     'user_data_header': user_data_header,
                     'user_data': user_data,
                     'user_data_all_url': user_data_all_url,
                     'user_pr_header': user_pr_header,
                     'user_pr': user_pr,
                     'user_pr_all_url': user_pr_all_url,
                     'user_fit_header': user_fit_header,
                     'user_fit': user_fit,
                     'user_fit_all_url': user_fit_all_url,
                     'breadcrumbs': breadcrumbs,
                     'post_url': reverse('sansanalysis.simpleplot.views.select_data'),
                     'sample_url': reverse('sansanalysis.simpleplot.views.sample_data')
                     }
    
    if error_msg is not None:
        template_args['user_alert']=[error_msg]
        
    template_args = _common_template_args(request, **template_args)
    
    return render_to_response('simpleplot/dashboard.html', 
                              template_args,
                              context_instance=RequestContext(request))

def _common_template_args(request, **template_args):
    """
        Fill the template argument items needed to populate
        the side bars and other satellite items on the pages.
        
        Only the arguments common to all pages will be filled.
    """
    # Add actions
    if not template_args.has_key('actions') or template_args['actions'] is None:
        template_args['actions'] = []
        
    if not template_args.has_key('user_alert') or template_args['user_alert'] is None:
        template_args['user_alert'] = []
                            
    if request.user.is_authenticated():
        # Check whether the user is registered. If not, show him a message 
        # suggesting that he clicks the link to register
        show_reg_popup = False
        try:
            p = request.user.get_profile().registered
            show_reg_popup = not p and not request.session.get("register_popup_shown", False)
        except:
            # The use might not have a profile
            error_msg = "_common_template_args: could not get profile\n  %s" % sys.exc_value
            #store_error(user=request.user, url=request.path, text=error_msg, method='simpleplot._common_template_args', build=sansanalysis.settings.APP_VERSION)
        if show_reg_popup:
            message = "Benefit from the full functionality of this site by <a href='%s' title='Click here to register'> registering</a>!" % reverse('sansanalysis.users.views.registration')
            template_args['user_alert'].append(message)
            request.session["register_popup_shown"] = True
        
        # Get the most recently viewed data
        template_args['recent_data'] = view_util.get_recent_data_by_user(request.user.id)
        #template_args['recent_fits'] = view_util.get_recent_prfits_by_user(request.user.id) 
        template_args['recent_fits'] = common_view_util.get_recent_data_computations_by_user(request.user.id) 
        
    else:
        template_args['actions'].append({'name': 'Log-in with your OpenID',
                                         'url': reverse('sansanalysis.users.views.startOpenID'),
                                         'attrs': [{'name' : 'title',
                                                    'value': "\"Benefit from the full data analysis functionality of this site by logging in!\""}]})
    
    
    return template_args
    
def _data_template_args(request, iq, **template_args):
    """
        Fill the template argument items needed to populate
        the side bars and other satellite items on the pages
        
        Arguments specific to a given data set will be filled.
    """
    template_args = _common_template_args(request, **template_args)
    
    if request.user.is_authenticated():
        # Get the most recent fits
        #TODO: change this to a call to common, to get all computations from all apps
        #template_args['recent_fits'] = view_util.get_recent_prfits_by_iqdata(request.user.id, iq.id)
        template_args['recent_fits'] = common_view_util.get_recent_data_computations_by_iqdata(request.user.id, iq.id)
            
        if len(template_args['recent_fits'])==0:
            template_args['user_alert'].append("<b>Hint</b>: use the action links above to perform fits.")
    
        # Check whether the user is the owner of the data
        if request.user.id == iq.owner:
            template_args['actions'].append({'name': 'Share this data',
                            'attrs': [{'name'  : 'onClick',
                                      'value' : "\"get_data_shared_key($, '%s', %s);\"" % (iq.name, iq.id)},
                                      {'name' : 'title',
                                       'value': "\"Click to generate a link that you can send other people you want to share this data set with.\""}]})
            template_args['actions'].extend(common_view_util.get_data_actions(iq.id))
        # Check whether the user has the data in his shared list
        elif manipulations.iqdata.has_shared_data(request.user, iq):
            template_args['actions'].extend(common_view_util.get_data_actions(iq.id))
    
        # Check whether the user loaded the data using a shared key
        elif view_util.has_shared_data_info(request, iq):
            template_args['actions'].append({'name': 'Store this data',
                            'url': reverse('sansanalysis.simpleplot.views.store_data', args=(manipulations.iqdata.get_data_shared_key(iq.id),)),
                            'attrs': [{'name' : 'title',
                                       'value': "\"Click to keep this data set in your permanent list of shared data. By doing so, you will no longer need to use the link provided to you to access the data.\""}]})

        # Check whether the user is the owner of the data
        if request.user.id == iq.owner or manipulations.iqdata.has_shared_data(request.user, iq):
            # Create an object in the trail of recently viewed data
            recent = RecentData(iq_data=iq, user_id=request.user.id)
            recent.save() 
    
    # Scale of the output plot 
    outscale = request.session.get('out_scale_x', default='linear')
    template_args['xoutscale_qs'] = view_util.OUTPUT_SCALE_X_QSTRING
        
    outscale = request.session.get('out_scale_y', default='linear')
    template_args['youtscale_qs'] = view_util.OUTPUT_SCALE_Y_QSTRING
        
    # Scale of the input I(q) plot
    iqscale = request.session.get('scale_x', default='linear')
    template_args['xscale_qs'] = view_util.DATA_SCALE_X_QSTRING
    template_args['xscale'] = iqscale
    
    iqscale = request.session.get('scale_y', default='linear')
    template_args['yscale'] = iqscale
    template_args['yscale_qs'] = view_util.DATA_SCALE_Y_QSTRING
    
    return template_args
    
def _process_plot_scale(request):
    
    # Scale of the output plot 
    outscale_x = request.GET.get(view_util.OUTPUT_SCALE_X_QSTRING, None)
    if outscale_x is not None:
        request.session[view_util.OUTPUT_SCALE_X_QSTRING] = outscale_x
        
    outscale_y = request.GET.get(view_util.OUTPUT_SCALE_Y_QSTRING, None)
    if outscale_y is not None:
        request.session[view_util.OUTPUT_SCALE_Y_QSTRING] = outscale_y
        
    # Scale of the input I(q) plot
    iqscale_x = request.GET.get(view_util.DATA_SCALE_X_QSTRING, None)
    if iqscale_x is not None:
        request.session[view_util.DATA_SCALE_X_QSTRING] = iqscale_x        
    
    iqscale_y = request.GET.get(view_util.DATA_SCALE_Y_QSTRING, None)
    if iqscale_y is not None:
        request.session[view_util.DATA_SCALE_Y_QSTRING] = iqscale_y        
    
    
@confirm_access    
def data_details(request, iq_id):
    """
        Present details about the data.
        
        #TODO: show meta data information if available
        
        @param iq_id: id of IqData object
    """
    
    iq = get_object_or_404(IqData, pk=iq_id)
    
    # Process GET arguments for plot scale
    _process_plot_scale(request)
    
    try:
        iq_data, ticks_x, ticks_y, errors = view_util.get_plottable_iq(request, iq)
    except:
        # Send user to error page
        err_id = store_error(user=request.user, url=request.path, text=sys.exc_value, method='simpleplot.views.data_details', is_shown=True, build=sansanalysis.settings.APP_VERSION)
        return render_to_response('simpleplot/error.html',
                                  {'error': 'Error ID = %s: Could not process data' % str(err_id)},
                                  context_instance=RequestContext(request))
        
    # Action list
    actions = []
        
    # Prepare the response
    breadcrumbs = "<a href='%s'>Home</a> &rsaquo; %s" % (reverse('sansanalysis.simpleplot.views.home'), iq.name) 
    
    template_args = {  'iq_data':str(iq_data),
                       'iq_id': iq_id,
                       'iq_name':iq.name,
                       'ticks_x': ticks_x,
                       'ticks_y': ticks_y,
                       'actions': actions,
                       'user_alert': errors,
                       'breadcrumbs': breadcrumbs}
    template_args = _data_template_args(request, iq, **template_args)
         
    return render_to_response('simpleplot/data_details.html', 
                              template_args,
                               context_instance=RequestContext(request))
       
@login_required
def get_estimates(request, iq_id):
    """
        Ajax call
    """
    try:        
        form_data = {}
        f = PrForm(request.GET)
        if f.is_valid():
            invertor = manipulations.prdata.PrInvertor()
            n_terms, alpha = invertor.estimate(iq_id, f.cleaned_data, request.user.id)
            resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<pr>\n<alpha>%-3.1g</alpha>\n<n_terms>%g</n_terms>\n</pr>" % (alpha, n_terms)
            return HttpResponse(resp, mimetype="text/xml")
        else: 
            raise RuntimeError, "PrForm could not be validated"
    except:
        error_msg = "get_estimates failed: %s" % sys.exc_value
        store_error(user=request.user, url=request.path, text=error_msg, method='simpleplot.get_estimates', build=sansanalysis.settings.APP_VERSION)

        resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<pr>\n<alpha>N/A</alpha>\n<n_terms>N/A</n_terms>\n</pr>" 
        return HttpResponse(resp, mimetype="text/xml")

@login_required
def explore_dmax(request, iq_id):
    """
         Ajax call
    """ 
    try:        
        form_data = {}
        f = PrForm(request.GET)
        if f.is_valid():
            
            expl_min = None
            expl_max = None
            expl_npt = 25
            try:
                value_in = request.GET.get('expl_min',None)
                if value_in is not None:
                    expl_min = float(value_in)
                
                value_in = request.GET.get('expl_max',None)    
                if value_in is not None:
                    expl_max = float(value_in)
                
                expl_npt = int(request.GET.get('expl_npt',25))
            except:
                err_mess = "explore_dmax: could not process exploration range\n"
                err_mess += "  Min:%s / Max:%s / Npts:%s\n" % (str(expl_min), str(expl_max), str(expl_npt))
                err_mess += "  %s" % sys.exc_value
                store_error(user=request.user, url=request.path, text=err_mess, method='simpleplot.explore_dmax', build=sansanalysis.settings.APP_VERSION)
            
            invertor = manipulations.prdata.PrInvertor()
            plotdata = invertor.explore_dmax(iq_id, f.cleaned_data, request.user.id, min=expl_min, max=expl_max, npts=expl_npt)
            
            resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<pr>\n"
            for i in range(len(plotdata['x'])):
                resp += "<point><x>%g</x><y>%g</y></point>\n" % (plotdata['x'][i], plotdata['y'][i])
            resp += "</pr>"
            return HttpResponse(resp, mimetype="text/xml")
        else:
            raise RuntimeError, "PrForm could not be validated"
    except:
        err_mess = "explore_dmax failed: %s" % sys.exc_value
        store_error(user=request.user, url=request.path, text=err_mess, method='simpleplot.explore_dmax', build=sansanalysis.settings.APP_VERSION)
        
        resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<pr></pr>"
        return HttpResponse(resp, mimetype="text/xml")
    
    
def access_shared_data(request, key):
    """
    """
    # Find the key and its associated data set
    iq = manipulations.iqdata.get_anonymous_shared_data(key)
    if iq is None:
        raise Http404
    
    #Store key in session
    request.session['data_shared_key'] = {}
    request.session['data_shared_key'][iq.id] = key
    
    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.data_details', args=(iq.id,)))    
    
@login_required 
@confirm_access    
def share_data(request, iq_id):
    """
        Popup that displays the shared key for a specific data set
    """
    # Get data information
    iq = get_object_or_404(IqData, pk=iq_id)

    # Check whether a key exists for this data
    key = manipulations.iqdata.get_data_shared_key(iq, create=True)
    
    permalink = reverse('sansanalysis.simpleplot.views.access_shared_data', args=(key,))
    permalink = sansanalysis.settings.APP_DOMAIN+permalink
        
    resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<key>%s</key>" % permalink
    return HttpResponse(resp, mimetype="text/xml")

    return render_to_response('simpleplot/share_popup.html', 
                           {'iq_data':iq.name,
                            'permalink': permalink},
                           context_instance=RequestContext(request))
@login_required    
def store_data(request, key):
    """
        Popup that displays the shared key for a specific data set
    """
    # Find the key and its associated data set
    iq = manipulations.iqdata.get_anonymous_shared_data(key)
    if iq is None:
        raise Http404
    
    # Verify that the link doesn't already exist
    manipulations.iqdata.create_shared_link(request.user, iq)
    
    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.data_details', args=(iq.id,)))    
    
@login_required
@confirm_access
def delete_data(request, iq_id):
    """
        Delete a data set
    """
    iq = get_object_or_404(IqData, pk=iq_id)

    # Check whether the user is the owner of the data
    if request.user.id == iq.owner:
        # Deactivate the data set / Stored links will be kept
        manipulations.iqdata.deactivate_data(iq)
    
    # Check whether the user has the data in his shared list
    elif manipulations.iqdata.has_shared_data(request.user, iq):
        # Delete the link between this user and the data set
        manipulations.iqdata.remove_shared_link(iq, request.user)
  
    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.select_data'))

def home(request):
    template_args = {}
    template_args = _common_template_args(request, **template_args)
    return render_to_response('simpleplot/index.html', 
                           template_args,
                           context_instance=RequestContext(request))

def about_site(request):
    breadcrumbs = "<a href='%s'>Home</a> &rsaquo; About" % reverse('sansanalysis.simpleplot.views.home')
    template_args = {'breadcrumbs': breadcrumbs,
                     'app_version': sansanalysis.settings.APP_VERSION}
    template_args = _common_template_args(request, **template_args)
    return render_to_response('simpleplot/about_site.html', 
                           template_args,
                           context_instance=RequestContext(request))

@login_required
def share_pr(request, iq_id, pr_id):
    """
        Ajax call
    """

    # Get data information
    iq = get_object_or_404(IqData, pk=iq_id)
    pr = PrInversion.objects.get(user_id=request.user.id, iq_data__id=iq_id, pk=pr_id)

    # Check whether a key exists for this data
    key = manipulations.prdata.get_pr_shared_key(pr, create=True)
        
    permalink = reverse('sansanalysis.simpleplot.views.access_shared_pr', args=(key,))
    permalink = sansanalysis.settings.APP_DOMAIN+permalink
    
    resp = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>\n<key>%s</key>" % permalink
    return HttpResponse(resp, mimetype="text/xml")
    
def access_shared_pr(request, key):
    """
    """
    # Find the key and its associated data set
    pr = manipulations.prdata.get_anonymous_shared_pr(key)
    if pr is None:
        raise Http404
    
    # Store key in session
    request.session['pr_shared_key'] = {}
    request.session['pr_shared_key'][pr.id] = key
    
    # Store data key in session, to let the user access the data
    data_key = manipulations.iqdata.get_data_shared_key(pr.iq_data, create=True)
    request.session['data_shared_key'] = {}
    request.session['data_shared_key'][pr.iq_data.id] = data_key
    
    # Check whether the user is authenticated, if not redirect them to the data page.
    
    if not request.user.is_authenticated():
        # Check whether a key exists for this data
        key = manipulations.iqdata.get_data_shared_key(pr.iq_data, create=True)
        permalink = reverse('sansanalysis.simpleplot.views.access_shared_data', args=(key,))
        permalink = sansanalysis.settings.APP_DOMAIN+permalink 
        
        welcome = "\"The computational functionality on this site is only available to registered users.<p>"
        welcome += "Please follow the instructions on this page to register in order to view the P(r) inversion fit you are trying to access.<p>"
        welcome += "Alternatively, you can follow the link below to view the data:<p>"
        welcome += "<a href='%s'>%s</a>\"" % (permalink, pr.iq_data.name)

        template_args = {'popup_alert': welcome}
        template_args = _common_template_args(request, **template_args)
        return render_to_response('simpleplot/index.html', 
                           template_args,
                           context_instance=RequestContext(request))
    
    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.invert', args=(pr.iq_data.id, pr.id,)))    
    
@login_required    
def store_pr(request, key):
    """
        Store the link to the PrInversion object corresponding to the given key
    """
    # Find the key and its associated data set
    pr = manipulations.prdata.get_anonymous_shared_pr(key)
    if pr is None:
        raise Http404
    
    # Verify that the link doesn't already exist
    manipulations.prdata.create_shared_link(request.user, pr)
    
    # Create a link to the data as well
    manipulations.iqdata.create_shared_link(request.user, pr.iq_data)
    
    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.invert', args=(pr.iq_data.id, pr.id)))    

@login_required
def delete_pr(request, iq_id, pr_id):
    """
        Delete a data set
    """
    pr = get_object_or_404(PrInversion, pk=pr_id)

    # Check whether the user is the owner of the fit
    if request.user.id == pr.user_id:
        # Deactivate the P(r) inversion for this user / shared links will be kept
        manipulations.prdata.deactivate_pr(pr)
    
    # Check whether the user has the data in his shared list
    elif manipulations.prdata.has_shared_pr(request.user, pr):
        # Delete the link between this user and the data set
        manipulations.prdata.remove_shared_link(pr, request.user)
  
    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.select_data'))

@login_required
def sample_data(request):
    """
        Load a sample file and add it to the user's data
    """
    iq_id = manipulations.iqdata.load_sample_data(request.user)
    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.select_data'))
    
    