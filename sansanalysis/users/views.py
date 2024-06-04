from django.contrib.auth.decorators import login_required
from django import http
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from django.template import RequestContext


from openid.consumer import consumer
from openid.consumer.discover import DiscoveryFailure
from openid.extensions import ax, pape, sreg
from openid.yadis.constants import YADIS_HEADER_NAME, YADIS_CONTENT_TYPE
from openid.server.trustroot import RP_RETURN_TO_URL_TYPE

from sansanalysis.users.openid_backend import get_token
from sansanalysis.users.models import UserProfile
import logging
import util

PAPE_POLICIES = [
    'AUTH_PHISHING_RESISTANT',
    'AUTH_MULTI_FACTOR',
    'AUTH_MULTI_FACTOR_PHYSICAL',
    ]

# List of (name, uri) for use in generating the request form.
POLICY_PAIRS = [(p, getattr(pape, p))
                for p in PAPE_POLICIES]

def getOpenIDStore():
    """
    Return an OpenID store object fit for the currently-chosen
    database backend, if any.
    """
    return util.getOpenIDStore('/tmp/djopenid_c_store', 'c_')

def getConsumer(request):
    """
    Get a Consumer object to perform OpenID authentication.
    """
    return consumer.Consumer(request.session, getOpenIDStore())

def renderIndexPage(request, **template_args):
    template_args['consumer_url'] = util.getViewURL(request, startOpenID)
    template_args['pape_policies'] = POLICY_PAIRS
    
    breadcrumbs = "<a href='%s'>Home</a> &rsaquo; <a href='%s'>Login</a>" % (reverse('sansanalysis.simpleplot.views.home'),
                                                      reverse('sansanalysis.users.views.startOpenID')) 
    template_args['breadcrumbs'] = breadcrumbs

    response =  direct_to_template(
        request, 'users/openid_signin.html', template_args)
    response[YADIS_HEADER_NAME] = util.getViewURL(request, rpXRDS)
    return response

def renderRegistrationPage(request, **template_args):
    breadcrumbs = "<a href='%s'>Home</a> &rsaquo; <a href='%s'>Registration</a>" % (reverse('sansanalysis.simpleplot.views.home'),
                                                      reverse('sansanalysis.users.views.registration')) 
    template_args['breadcrumbs'] = breadcrumbs
    return direct_to_template(
        request, 'users/registration.html', template_args)

def startOpenID(request):
    """
    Start the OpenID authentication process.  Renders an
    authentication form and accepts its POST.

    * Renders an error message if OpenID cannot be initiated

    * Requests some Simple Registration data using the OpenID
      library's Simple Registration machinery

    * Generates the appropriate trust root and return URL values for
      this application (tweak where appropriate)

    * Generates the appropriate redirect based on the OpenID protocol
      version.
    """
    # request.session['pr_shared_key'] = {}
    get_next = request.GET.get('next', None) 
    if get_next is not None:
        request.session['signin_next'] = get_next
    
    if request.POST:
        # Start OpenID authentication.
        openid_url = request.POST['openid_identifier']
        c = getConsumer(request)
        error = None

        try:
            auth_request = c.begin(openid_url)
        except DiscoveryFailure, e:
            # Some other protocol-level failure occurred.
            error = "OpenID discovery error: %s" % (str(e),)

        if error:
            # Render the page with an error.
            return renderIndexPage(request, error=error)
        
        # Add Attribute Exchange request information.
        ax_request = ax.FetchRequest()
        ax_request.add(
            ax.AttrInfo('http://axschema.org/contact/email',
                        required=True))
        
        auth_request.addExtension(ax_request)

        # Add PAPE request information.  We'll ask for
        # phishing-resistant auth and display any policies we get in
        # the response.
        requested_policies = []
        policy_prefix = 'policy_'
        for k, v in request.POST.iteritems():
            if k.startswith(policy_prefix):
                policy_attr = k[len(policy_prefix):]
                if policy_attr in PAPE_POLICIES:
                    requested_policies.append(getattr(pape, policy_attr))

        if requested_policies:
            pape_request = pape.Request(requested_policies)
            auth_request.addExtension(pape_request)

        # Compute the trust root and return URL values to build the
        # redirect information.
        trust_root = util.getViewURL(request, startOpenID)
        return_to = util.getViewURL(request, finishOpenID)

        # Send the browser to the server either by sending a redirect
        # URL or by generating a POST form.
        if auth_request.shouldSendRedirect():
            url = auth_request.redirectURL(trust_root, return_to)
            return HttpResponseRedirect(url)
        else:
            # Beware: this renders a template whose content is a form
            # and some javascript to submit it upon page load.  Non-JS
            # users will have to click the form submit button to
            # initiate OpenID authentication.
            form_id = 'openid_message'
            form_html = auth_request.formMarkup(trust_root, return_to,
                                                False, {'id': form_id})
            
            redirect_url = auth_request.redirectURL(trust_root, return_to)
            return HttpResponseRedirect(redirect_url)            

    return renderIndexPage(request)

def finishOpenID(request):
    """
    Finish the OpenID authentication process.  Invoke the OpenID
    library with the response from the OpenID server and render a page
    detailing the result.
    """
    result = {}

    # Because the object containing the query parameters is a
    # MultiValueDict and the OpenID library doesn't allow that, we'll
    # convert it to a normal dict.

    # OpenID 2 can send arguments as either POST body or GET query
    # parameters.
    request_args = util.normalDict(request.GET)
    if request.method == 'POST':
        request_args.update(util.normalDict(request.POST))

    if request_args:
        c = getConsumer(request)

        # Get a response object indicating the result of the OpenID
        # protocol.
        return_to = util.getViewURL(request, finishOpenID)

        response = c.complete(request_args, return_to)
        
        # Get a Simple Registration response object if response
        # information was included in the OpenID response.
        email = None
        if response.status == consumer.SUCCESS:
            ax_response = ax.FetchResponse.fromSuccessResponse(response)
            if ax_response:
                try:
                    email = ax_response.get('http://axschema.org/contact/email')[0]
                except:
                    logging.error("users.views.finishOpenID: could not get user email")

        # Map different consumer status codes to template contexts.
        results = {
            consumer.CANCEL:
            {'message': 'OpenID authentication cancelled.'},

            consumer.FAILURE:
            {'error': 'OpenID authentication failed.'},

            consumer.SUCCESS:
            {'url': response.getDisplayIdentifier()}
        }

        #http://www.gravatar.com/avatar/6bb6ad4a6958e74380e755549d8e03ca?s=128&d=monsterid
        result = results[response.status]

        if isinstance(response, consumer.SuccessResponse):
            user = authenticate(username=response.getDisplayIdentifier(), password=get_token())
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                       
                    # Check whether this login gives us profile/registration info we didn't have
                    if email is not None:
                        try:
                            profile = user.get_profile()
                            if not profile.registered:
                                # User is not registered and we have an email. Use the info.
                                user.email = email
                                profile.set_gravatar(email)
                                try:
                                    user.username = email.split('@')[0]
                                except:
                                    # Could not parse the email - not a problem
                                    pass
                                user.save()
                                profile.registered = True
                                profile.save()
                        except:
                            # User doesn't have a profile: probably a local user - not a problem
                            pass

                    # Check whether we came to the login screen from a site URL
                    signin_next = request.session.get('signin_next', None)
                    if signin_next is not None:
                        request.session['signin_next'] = None
                        return HttpResponseRedirect(signin_next)
                    # If not, check whether we need registration
                    try:
                        if not user.get_profile().registered:
                            return HttpResponseRedirect(reverse('sansanalysis.users.views.registration'))
                    except:
                        # User has no profile. Not a problem.
                        pass
                    # If not, go to the dashboard
                    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.select_data'))
                else:
                    logging.error("users.views.finishOpenID: blocked user tried to log in: %s" % response.getDisplayIdentifier())
                    result['failure_reason'] = 'Your account is currently blocked. Please contact the site administrator.'
            else:
                # This should never happen. 
                logging.error("users.views.finishOpenID: authenticated OpenID with None User object")
                result['failure_reason'] = 'We are experiencing problems with your account. Please try again or contact the site administrator.'
            
        elif isinstance(response, consumer.FailureResponse):
            # In a real application, this information should be
            # written to a log for debugging/tracking OpenID
            # authentication failures. In general, the messages are
            # not user-friendly, but intended for developers.
            result['failure_reason'] = response.message

    return renderIndexPage(request, **result)

def rpXRDS(request):
    """
    Return a relying party verification XRDS document
    """
    return util.renderXRDS(
        request,
        [RP_RETURN_TO_URL_TYPE],
        [util.getViewURL(request, finishOpenID)])

@login_required
def registration(request):
    """
        Registration form for first-time users
    """
    from forms import RegistrationForm
    
    if request.method == 'POST': 
        form = RegistrationForm(request.POST) 
        if form.is_valid(): 
            # File out the User information
            request.user.username   = form.cleaned_data['username']
            request.user.first_name = form.cleaned_data['firstname']
            request.user.last_name  = form.cleaned_data['lastname']
            request.user.email      = form.cleaned_data['email']
            request.user.save()
            
            # File out the extra profile information in UserProfile
            try:
                profile = request.user.get_profile()
                profile.registered = True
                profile.set_gravatar(form.cleaned_data['email'])
                profile.save()
            except UserProfile.DoesNotExist:
                # Profile doesn't exist: only happens for local users (staff)
                # We don't allow the creation of a profile in this case
                logging.error("users.views.registration: skipping UserProfile update for %s" % request.user.username)
            
            return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.select_data'))              
    else:            
        prepop = {'firstname':   request.user.first_name,
                  'lastname': request.user.last_name,
                  'email': request.user.email}
        
        # Only fill in the username if the user is already registered
        try:
            profile = request.user.get_profile()
            if profile.registered:
                prepop['username'] = request.user.username
        except UserProfile.DoesNotExist:
            prepop['username'] = request.user.username
            logging.error("users.views.registration: no user profile available for %s" % request.user.username)
            
      
        form = RegistrationForm(initial = prepop) 
    
    template_args = {'form': form}
    return renderRegistrationPage(request, **template_args)

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.home'))      