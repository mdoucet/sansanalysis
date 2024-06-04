import sys, numpy, time, math
import hashlib

# Application imports
import sansanalysis.simpleplot.calculations.invert_pr as invert_pr
from sansanalysis.simpleplot.models import PrInversion, PrOutput, IqData, PrCoefficients, AnonymousSharedPr, UserSharedPr
import sansanalysis.simpleplot.manipulations.iqdata as iqdata
from sansanalysis.app_logging.models import store_error
import sansanalysis.settings

def get_pr_output_id(pr_id):
    """
        Returns a PrOutput ID for a given PrInversion pk
        
        @param pr_id: pk of PrInversion
    """    
    try:
        return PrOutput.objects.get(inversion__id=pr_id).id
    except PrOutput.DoesNotExist:
        return None

class PrInvertor:
    """
    """
    def __init__(self):
        self.errors = []
        self.messages = []        
    
    def has_errors(self):
        """
            Returns True if errors were found during the last load
        """
        return len(self.errors)>0
    
    def __call__(self, iq_id, form_data, user_id):
        """
            Called after a P(r) inversion POST 
        """
        self.errors = []
        self.messages = []
           
        # Check that a data set is available
        # Get the data information to be displayed
        [iq] = IqData.objects.filter(pk=iq_id)
        
        iq_calc = []
        pr_calc = []
        
        # Provide and error box for computation-related errors.
        try:
            # Load data from file
            #TODO: replace this by DB access
            loader = iqdata.FileDataLoader()
            data_info = loader.load_file_data(iq)
            if data_info is None:
                error_msg = "Could not read file [iq_id=%s]. User ID = %s" % (str(iq.id), str(user_id))
                store_error(user=None, url=None, text=error_msg, method='prdata.PrInvertor.__call__', build=sansanalysis.settings.APP_VERSION)
                raise RuntimeError, "Data loader could not read the data file [ID=%s]." % str(iq.id)
            
            if data_info.dy is None or len(data_info.dy) != len(data_info.x) or all(v == 0 for v in data_info.dy):
                data_info.dy = numpy.ones(len(data_info.x))

            invertor = invert_pr.PrCalculation(form_data)
            iqfit, prfit, out_pars = invertor(data_info)
            
            # Keep track of errors
            self.messages.extend(invertor.messages)
            self.errors.extend(invertor.errors)   
            
            # Store inversion data
            q_min = form_data['q_min'] if form_data['q_min'] is not None else min(iqfit['x'])
            q_max = form_data['q_max'] if form_data['q_max'] is not None else max(iqfit['x'])
            problem = PrInversion(iq_data     = iq,
                                  user_id     = user_id,
                                  has_bck     = form_data['has_bck'],
                                  d_max       = form_data['d_max'],
                                  n_terms     = form_data['n_terms'],
                                  slit_height = form_data['slit_height'],
                                  slit_width  = form_data['slit_width'],
                                  alpha       = form_data['alpha'],
                                  q_min       = q_min,
                                  q_max       = q_max)
            problem.save()    
            
            # Store inversion output
            try:
                output = PrOutput(inversion = problem,
                                  chi2 = out_pars['chi2'],
                                  rg   = out_pars['rg'],
                                  bck  = out_pars['bck'],
                                  iq_zero = out_pars['iq_zero'],
                                  osc  = out_pars['osc'],
                                  pos_frac = out_pars['pos_frac'],
                                  pos_frac_1sigma = out_pars['pos_frac_1sigma'])
                output.save()
            except:
                output = PrOutput(inversion = problem,
                                  chi2 = 0,
                                  rg   = 0,
                                  bck  = 0,
                                  iq_zero = 0,
                                  osc  = 0,
                                  pos_frac = 0,
                                  pos_frac_1sigma = 0)
                output.save()
                
                error_msg = "Could not save PrOutput\n"
                error_msg += "chi2=%s; rg=%s, bck=%s, iq0=%s, osc=%s, pos=%s, sig=%s" % (out_pars['chi2'],
                                                                                         out_pars['rg'],
                                                                                         out_pars['bck'],
                                                                                         out_pars['iq_zero'],
                                                                                         out_pars['osc'],
                                                                                         out_pars['pos_frac'],
                                                                                         out_pars['pos_frac_1sigma'])
                store_error(user=None, url=None, text=error_msg, method='prdata.PrInvertor.__call__', build=sansanalysis.settings.APP_VERSION)
                raise
                
            # Store output coefficients and covariance matrix
            self._save_coefficients(output, out_pars['coeff'], out_pars['cov'])
            #self._check_coefficients_storage(output.id, out_pars['coeff'], out_pars['cov'])
            
        except:
            error_msg = "Could not compute P(r)\n%s" % sys.exc_value
            store_error(user=None, url=None, text=error_msg, method='prdata.PrInvertor.__call__', build=sansanalysis.settings.APP_VERSION)
            raise
           
        iqfit['iq_id'] = iq_id
        prfit['iq_id'] = iq_id
        
        return iqfit, prfit, problem.id

    def _save_coefficients(self, pr_output, out, cov):
        """
            Store P(r) inversion output coefficents to DB
            @param pr_output: PrOutput model object
            @param out: output coefficient
            @param cov: covariance matrix
        """
        for i in range(len(out)):
            c = PrCoefficients(proutput   = pr_output,
                               type       = 0,
                               main_index = i,
                               value      = out[i])
            c.save()
            
            if False:
                for j in range(len(out)):
                    cc = PrCoefficients(proutput   = pr_output,
                                         type       = 1,
                                         main_index = i,
                                         sec_index  = j,
                                         value = cov[i][j])
                    cc.save()
    
    def _load_coefficients(self, pr_output_id):
        """
            @param pr_output_id: primary key of PrOutput model object
            @param out: output coefficient
            @param cov: covariance matrix
        """
        t_0 = time.time()
        c = PrCoefficients.objects.filter(proutput__pk=pr_output_id, type=0).order_by('main_index')
        
        out = numpy.zeros(len(c))
        cov = numpy.zeros([len(c), len(c)])
        
        for i in range(len(c)):
            out[i] = c[i].value
        
            cc = PrCoefficients.objects.filter(proutput__pk=pr_output_id, type=1, main_index=i).order_by('sec_index')
            for j in range(len(cc)):
                cov[i][j] = cc[j].value
        
        elapsed = time.time()-t_0
           
        return out, cov
    
    def _check_coefficients_storage(self, pr_output_id, out, cov):
        """
            Test the storage of the P(r) output coefficients
            
            @param pr_output_id: primary key of PrOutput model object
            @param out: output coefficient
            @param cov: covariance matrix
        """
        _out, _cov = self._load_coefficients(pr_output_id)
        
        assert(len(out)==len(_out))
        assert(len(cov)==len(_cov))
        
        errors = False
        for i in range(len(_out)):
            if math.fabs(out[i]-_out[i])>1e-6:
                error_msg = "coefficients: loaded data doesn't match stored data %g, %g" % (out[i], out[i])
                store_error(user=None, url=None, text=error_msg, method='prdata.PrInvertor._check_coefficients_storage', build=sansanalysis.settings.APP_VERSION)
                errors = True
            
            for j in range(len(_out)):
                if math.fabs(cov[i][j]-_cov[i][j])>1e-6:
                    error_msg = "covariance[%d][%d]: loaded data doesn't match stored data %g, %g" % (i, j, cov[i][j], _cov[i][j])
                    store_error(user=None, url=None, text=error_msg, method='prdata.PrInvertor._check_coefficients_storage', build=sansanalysis.settings.APP_VERSION)
                    errors = True
        
        if errors:
            raise RuntimeError, "Test failed: loaded data doesn't match stored data"
        
    def get_iq_calc(self, pr_output_id):
        """
        """
        
        pr = PrOutput.objects.filter(pk=pr_output_id)
        if len(pr)==0:
            raise RuntimeError, "No PrOutput model object found with pk=%d" % pr_output_id 
        
        iq_data = pr[0].inversion.iq_data
        loader = iqdata.FileDataLoader()
        data_info = loader.load_file_data(iq_data)
        if data_info is None:
            error_msg = "Could not read file [iq_id=%s]" % str(iq_data.id)
            store_error(user=None, url=None, text=error_msg, method='prdata.PrInvertor.get_iq_calc', build=sansanalysis.settings.APP_VERSION)
            raise RuntimeError, "Data loader could not read the data file [ID=%s]." % str(iq_data.id)
      
        if data_info.dy is None or len(data_info.dy) != len(data_info.x) or all(v == 0 for v in data_info.dy):
            data_info.dy = numpy.ones(len(data_info.x))
        
        out, cov = self._load_coefficients(pr_output_id)
        
        parameters = pr[0].inversion.get_parameters()
        
        invertor = invert_pr.PrCalculation(parameters)
        
        qmin = parameters['q_min'] if parameters['q_min'] else min(data_info.x)
        qmax = parameters['q_max'] if parameters['q_max'] else max(data_info.x)
        
        xdist = []
        for x in data_info.x:
            if x>=qmin and x<=qmax:
                xdist.append(x) 
        
        iq_calc = invertor.get_iq_calc(xdist, out, cov)
        
        # Keep track of errors
        self.messages.extend(invertor.messages)
        self.errors.extend(invertor.errors)           
        
        return {'iq_id':iq_data.id,
                'x':xdist,
                'y':iq_calc,
                'dy':None}
        
        
    def get_pr(self, pr_output_id):
        """
        """
        
        pr = PrOutput.objects.filter(pk=pr_output_id)
        if len(pr)==0:
            raise RuntimeError, "No PrOutput model object found with pk=%d" % pr_output_id 
        
        out, cov = self._load_coefficients(pr_output_id)
        
        invertor = invert_pr.PrCalculation(pr[0].inversion.get_parameters())
        
        r, pr_calc = invertor.get_pr(out, cov)
        return {'iq_id':pr[0].inversion.iq_data.id,
                'x':r,
                'y':pr_calc,
                'dy':None}
        
    def get_outputs(self, pr_output_id):
        """
            Return a dictionary of P(r) inversion output 
            parameters
            
            @param pr_output_id: pk of PrOutput item
        """
        pr = PrOutput.objects.filter(pk=pr_output_id)
        if len(pr)==0:
            raise RuntimeError, "No PrOutput model object found with pk=%d" % pr_output_id 

        outputs = []
        outputs.append({'name':'Chi <span class="exponent">2</span>',
                        'title':'\"Chi squared over degrees of freedom\"',
                        'value':pr[0].chi2,
                        'units':''})
        outputs.append({'name':'Rg',
                        'title':'\"Radius of gyration\"',
                        'value':pr[0].rg,
                        'units':'&Aring;'})
        outputs.append({'name':'Bck',
                        'title':'\"Background value\"',
                        'value':pr[0].bck,
                        'units':'1/&Aring;'})
        outputs.append({'name':'I(Q=0)',
                        'title':'\"Intensity at Q=0\"',
                        'value':pr[0].iq_zero,
                        'units':'1/&Aring;'})
        outputs.append({'name':'Osc',
                        'title': '\"Oscillation parameter: the greater the number, the more oscillations P(r) has\"', 
                        'value':pr[0].osc})
        outputs.append({'name':'R <span class="exponent">+</span>',
                        'title':'\"Fraction of the integral of P(r) that is above zero\"',
                        'value':pr[0].pos_frac,
                        'units':''})
        outputs.append({'name':'R <span class="exponent">++</span>',
                        'title':'\"Fraction of the integral of P(r) that is at least one standard deviation above zero\"',
                        'value':pr[0].pos_frac_1sigma,
                        'units':''})
        return outputs
        
    def estimate(self, iq_id, form_data, user_id):

        # Check that a data set is available
        # Get the data information to be displayed
        [iq] = IqData.objects.filter(pk=iq_id)
        
        try:
            # Load data from file
            #TODO: replace this by DB access
            loader = iqdata.FileDataLoader()
            data_info = loader.load_file_data(iq)
            if data_info is None:
                error_msg = "Could not read file [iq_id=%s]" % str(iq.id)
                store_error(user=None, url=None, text=error_msg, method='prdata.PrInvertor.estimate', build=sansanalysis.settings.APP_VERSION)
                raise RuntimeError, "Data loader could not read the data file [ID=%s]." % str(iq.id)
           
            if data_info.dy is None or len(data_info.dy) != len(data_info.x) or all(v == 0 for v in data_info.dy):
                data_info.dy = numpy.ones(len(data_info.x))

            invertor = invert_pr.PrCalculation(form_data)
            n_terms, alpha, message = invertor.estimate(data_info)
            return n_terms, alpha
            
        except:
            store_error(user=None, url=None, text=sys.exc_value, method='prdata.PrInvertor.estimate', build=sansanalysis.settings.APP_VERSION)
            raise
        

    def explore_dmax(self, iq_id, form_data, user_id, min=None, max=None, npts=25):
        # Check that a data set is available
        # Get the data information to be displayed
        [iq] = IqData.objects.filter(pk=iq_id)
        
        try:
            # Load data from file
            #TODO: replace this by DB access
            loader = iqdata.FileDataLoader()
            data_info = loader.load_file_data(iq)
            if data_info is None:
                error_msg = "Could not read file [iq_id=%s]" % str(iq.id)
                store_error(user=None, url=None, text=error_msg, method='prdata.PrInvertor.explore_dmax', build=sansanalysis.settings.APP_VERSION)
                raise RuntimeError, "Data loader could not read the data file [ID=%s]." % str(iq.id)
           
            if data_info.dy is None or len(data_info.dy) != len(data_info.x) or all(v == 0 for v in data_info.dy):
                data_info.dy = numpy.ones(len(data_info.x))

            invertor = invert_pr.PrCalculation(form_data)
            results = invertor.explore_dmax(data_info, min, max, npts)
            
            return {'iq_id':iq_id,
                'x':results.d_max,
                'y':results.chi2,
                'dy':None}
        except:
            store_error(user=None, url=None, text=sys.exc_value, method='prdata.PrInvertor.explore_dmax', build=sansanalysis.settings.APP_VERSION)
            raise
        
        
def get_pr_shared_key(pr, create=False):
    """
        Get a key for a given PrInversion object to be shared.
        @param iq: PrInversion object
        @param create: if True, a link will be created if none is found
    """
    keys = AnonymousSharedPr.objects.filter(inversion=pr)
    if len(keys)==0:
        if create:
            key = hashlib.md5("%s%f" % (pr.id, time.time())).hexdigest()
            key_object = AnonymousSharedPr(shared_key=key, inversion=pr)
            key_object.save()
            return key
        else:
            return None
    else: 
        return keys[0].shared_key

        
def get_anonymous_shared_pr(key):
    """
        Retrieve PrInversion object by key
        @param key: shared key 
    """
    shared_data = AnonymousSharedPr.objects.filter(shared_key=key)
    if len(shared_data)==1:
        return shared_data[0].inversion
    elif len(shared_data)>1:
        raise RuntimeError, "prdata.get_anonymous_shared_pr: shared_key not unique!"
    return None
        
def get_pr(pr_id, user_id, iq_id, key=None):
    """
        Retrieve a pr inversion object from the database, with verification.    
        
        @param pr_id: PK of PrInversion object
        @param iq_id: PK of IqData obejct (for verification)
        @param user_id: PK of owner
        @param key: if not none, will confirm authorization if iq_id and user_id are not verified.
         
    """
    try:  
        pr = PrInversion.objects.get(user_id=user_id, iq_data__id=iq_id, pk=pr_id)
        return pr
    except PrInversion.DoesNotExist:
        # If we found no object, check whether the user has stored this fit
        try:
            if has_shared_pr_by_id(user_id, pr_id):
                return PrInversion.objects.get(pk=pr_id)
        except:
            # If we found no object, check whether the user has access through a shared key
            try:
                pr = PrInversion.objects.get(pk=pr_id)
                db_key = get_pr_shared_key(pr, create=False)
                if key==db_key:
                    return pr
            except PrInversion.DoesNotExist:
                # No such object
                return None
    
    except PrInversion.MultipleObjectsReturned:
        # we should never be here: log this event
        error_msg = "prdata.get_pr: go multiple PrInversion objects for unique PK\n  %s" % sys.exc_value
        store_error(user=None, url=None, text=error_msg, method='prdata.get_pr', build=sansanalysis.settings.APP_VERSION)
    
    return None
    
def create_shared_link(user, pr):
    """
        Create a UserSharePr link between the user
        and a PrInversion object if it doesn't already exist
        
        Returns the link
    """
    # Verify that the link doesn't already exist
    old_shared = UserSharedPr.objects.filter(inversion=pr, user=user)
    if len(old_shared)==0:
        shared = UserSharedPr(inversion=pr, user=user)
        shared.save()
        return shared
    else:
        return old_shared[0]
    
def has_shared_pr(user, pr):
    """
        Returns True if the specified user has a shared data link
        to the specified IqData object.
        @param iq: PrInversion object
        @param user: User object
    """
    shared = UserSharedPr.objects.filter(inversion=pr, user=user)
    return len(shared)>0

def has_shared_pr_by_id(user_id, pr_id):
    """
        Returns True if the specified user has a shared data link
        to the specified IqData object.
        @param iq_id: PK ofPrInversion object
        @param user_id: PK of User object
    """
    shared = UserSharedPr.objects.filter(inversion__id=pr_id, user__id=user_id)
    return len(shared)>0

def deactivate_pr(pr):
    """
        Deactivate a P(r) fit. Since many tables have PrInversion foreign keys, 
        we do not delete the data set. We simply change the owner to user ID = 0.
        That will prevent the data set to ever show up in the user's list of
        data and he will lose access to it.
        This solution will also enable a shared P(r) inversion to remain with
        the users it was shared with.
        
        Return true if we removed shared links
    """
    pr.user_id = 0
    pr.save()
    
    return False

def remove_shared_link(pr, user=None):
    """
        Remove all links to a P(r) fit.
        If a user is specified, remove links only for this user.
    """
    if user is None:
        shared = UserSharedPr.objects.filter(inversion=pr)
    else:
        shared = UserSharedPr.objects.filter(inversion=pr, user=user)
    
    has_links = len(shared)>0
    
    # Delete the links
    shared.delete()

    return has_links
