from sans.pr.invertor import Invertor
from sans.pr.distance_explorer import DistExplorer
import numpy
import math, sys

class PrCalculation:
    
    def __init__(self, parameters=None):
        self.errors = []
        self.messages = []
        
        self.invertor = Invertor()
        if parameters is not None:
            self.invertor.d_max = parameters['d_max']
            self.invertor.nfunc = parameters['n_terms']
            if parameters['q_min'] is not None:
                self.invertor.q_min = parameters['q_min']
            if parameters['q_max'] is not None:
                self.invertor.q_max = parameters['q_max']
            self.invertor.alpha = parameters['alpha']
            if parameters['slit_height'] is not None:
                self.invertor.slit_height = parameters['slit_height']
            if parameters['slit_width'] is not None:
                self.invertor.slit_width = parameters['slit_width']
            if parameters['has_bck'] is not None:
                self.invertor.has_bck = parameters['has_bck']
            
    def _setup_inversion(self, data_info):
        """
            Set up the inversion object
        """
        self.errors   = []
        self.messages = []

        # Sanity check
        if data_info is None:
            raise RuntimeError, "invert_pr.invert: expected a dictionary of data and got None"
    
        idx = [ i for i in range(len(data_info.x)) if data_info.x[i]>0 ]
    
        self.invertor.x   = data_info.x[idx]
        self.invertor.y   = data_info.y[idx]
        
        if len(data_info.x) != len(self.invertor.x):
            npts = len(data_info.x)-len(self.invertor.x)
            if npts==1:
                self.messages.append("A q-value was skipped because it was negative or equal to zero.")
            elif npts>1:
                self.messages.append("%d q-values were skipped because they were negative or equal to zero." % npts)
        
        # If we have no errors, add statistical errors
        if data_info.dy==None and self.invertor.y is not None:
            err = numpy.zeros(len(self.invertor.y))
            scale = None
            min_err = 0.0
            for i in range(len(self.invertor.y)):
                # Scale the error so that we can fit over several decades of Q
                if scale==None:
                    scale = 0.05*math.sqrt(self.invertor.y[i])
                    min_err = 0.01*self.invertor.y[i]
                err[i] = scale*math.sqrt( math.fabs(self.invertor.y[i]) ) + min_err
            message = "The loaded file had no error bars, statistical errors are assumed."
            self.invertor.err = err
        else:
            self.invertor.err = data_info.dy[idx]
        
    
    def __call__(self, data_info):
        """
            Perform inversion
        """
        # Set up the inversion object
        self._setup_inversion(data_info)
        
        # Perform inversion
        out, cov = self.invertor.invert(self.invertor.nfunc)
        
        # Store outputs 
        out_pars = {}
        
        def _check_float(value):
            if numpy.isnan(value): return None
            return value
        
        try:
            out_pars['chi2']     = _check_float(self.invertor.chi2)
            out_pars['rg']       = _check_float(self.invertor.rg(out))
            out_pars['bck']      = _check_float(self.invertor.background)
            out_pars['iq_zero']  = _check_float(self.invertor.iq0(out))
            out_pars['osc']      = _check_float(self.invertor.oscillations(out))
            out_pars['pos_frac'] = _check_float(self.invertor.get_positive(out))
            out_pars['pos_frac_1sigma']  = _check_float(self.invertor.get_pos_err(out, cov))
            out_pars['coeff']    = out
            out_pars['cov']      = cov
        except:
            raise RuntimeError, "perform_pr_inversion: error computing output parameters\n%s" % sys.exc_value
        
        
        # Compute I(q)
        iq_calc = self.get_iq_calc(data_info.x, out, cov)
        r, pr   = self.get_pr(out, cov)
            
        # Put distributions together
        iqfit = {'x':data_info.x,
                 'y':iq_calc,
                 'dy':None}
        
        prfit = {'x':r,
                 'y':pr,
                 'dy':None}
    
        return iqfit, prfit, out_pars
        
    
    def get_iq_calc(self, q, out, cov):
        """
            Compute calculated I(q) given the output of 
            a P(r) inversion
        """
        # By default, we assume no smearing
        evaluation_function = self.invertor.iq        
        # If we have used slit smearing, plot the smeared I(q) too
        if self.invertor.slit_width>0 or self.invertor.slit_height>0:
            evaluation_function = self.invertor.iq_smeared

        n_skip = 0
        iq_calc = numpy.zeros(len(q))
        for i in range(len(q)):
            if q[i]>0:
                iq_calc[i] = evaluation_function(out, q[i])
            else:
                n_skip += 1
                iq_calc[i] = 0
    
        if n_skip==1:
            self.messages.append("A q-value was skipped because it was negative or equal to zero.")
        elif n_skip>1:
            self.messages.append("%d q-values were skipped because they were negative or equal to zero." % n_skip)
            
        return iq_calc
    
    def get_pr(self, out, cov, npts=50):
        """
            Compute P(r) given the output of 
            a P(r) inversion
        """
        pr = numpy.zeros(npts)
        r  = numpy.zeros(npts)
        for i in range(npts):
            r[i] = self.invertor.d_max/(npts-1.0)*i
            pr[i] = self.invertor.pr(out, r[i])
            
        return r, pr
    
    def estimate(self, data_info):
        """    
            Estimate the number of terms and alpha given
            the input data
            @param data_info: Data1D object
        """
        # Set up the inversion object
        self._setup_inversion(data_info)
        
        return self.invertor.estimate_numterms()
    
    def explore_dmax(self, data_info, min, max, npts=25):
        """
            Explore output parameters for a range of D_max.
            
            @param min: minimum value for D_max
            @param max: maximum value for D_max
            @param npts: number of points for D_max
        """
        
        # Set up the inversion object
        self._setup_inversion(data_info) 
        
        explo = DistExplorer(self.invertor)
        return explo(min, max, npts)
    