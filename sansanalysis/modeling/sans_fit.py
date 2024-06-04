import numpy
from scipy import optimize
from sans.dataloader.data_info import Data1D

class Parameter:
    """
        Class to handle model parameters
    """
    def __init__(self, model, name, value=None, id=None):
            self.model = model
            self.name  = name
            self.id    = id
            if not value==None:
                self.model.setParam(self.name, value)
           
    def set(self, value):
        """
            Set the value of the parameter
        """
        self.model.setParam(self.name, value)

    def __call__(self):
        """ 
            Return the current value of the parameter
        """
        return self.model.getParam(self.name)
    

class SansFit():
    
    def __init__(self, model, data, fit_params=[], smearer=None, qmin=None, qmax=None):
        """
            @param data: Data1D object
            @param smearer: Smearer object. If supplied, will override the smearing info is part of Data1D
        """ 
        ## SANS model
        self.model = model
        ## Fit parameters
        self.fit_params = fit_params
        ## Smearer object
        self.smearer = smearer
        ## Data
        self.data = data
        
        # Sanity check
        if len(data.x) != len(data.y):
            raise RuntimeError, "sans_fit.SansFit: x and y have different lengths"

        ## Processed errors
        # Keep the errors separate from the data so that we don't over-right the original array
        if data.dy is None or len(data.dy) != len(data.x) or all(v == 0 for v in data.dy):
            self.dy = numpy.ones(len(data.x))
        else:
            self.dy = data.dy
    
        ## Set Q range
        self.set_q_range(qmin, qmax)
        
    def set_q_range(self, qmin=None, qmax=None):
        """ 
            Set q range for fitting
            
            @param qmin: minimum Q
            @param qmax: maximum Q
        """
        if qmin==None: self.qmin = min(self.data.x)
        else:          self.qmin=float(qmin)
            
        if qmax==None: self.qmax = max(self.data.x)
        else:          self.qmax=float(qmax)
            
        # Determine the range needed in unsmeared-Q to cover
        # the smeared Q range
        self._qmin_unsmeared = self.qmin
        self._qmax_unsmeared = self.qmax    
        
        self._first_unsmeared_bin = 0
        self._last_unsmeared_bin  = len(self.data.x)-1
        
        if self.smearer!=None:
            self._first_unsmeared_bin, self._last_unsmeared_bin = self.smearer.get_bin_range(self.qmin, self.qmax)
            self._qmin_unsmeared = self.data.x[self._first_unsmeared_bin]
            self._qmax_unsmeared = self.data.x[self._last_unsmeared_bin]
            
        # Identify the bin range for the unsmeared and smeared spaces
        self.idx = (self.data.x>=self.qmin) & (self.data.x <= self.qmax)
        self.idx_unsmeared = (self.data.x>=self._qmin_unsmeared) & (self.data.x <= self._qmax_unsmeared)
  

    def residuals(self, params=None):
        """ 
            Compute residuals.
            
            If self.smearer has been set, use if to smear
            the data before computing chi squared.
            
            @param params: dict of fit parameter values
            @return residuals
        """
        # Set the model parameters
        if params is not None:
            for i in range(len(self.fit_params)):
                self.fit_params[i].set(params[i])
        
        # Compute theory data f(x)
        fx= numpy.zeros(len(self.data.x))
        fx[self.idx_unsmeared] = self.model.evalDistribution(self.data.x[self.idx_unsmeared])
       
        ## Smear theory data
        if self.smearer is not None:
            fx = self.smearer(fx, self._first_unsmeared_bin, self._last_unsmeared_bin)
       
        ## Sanity check
        if numpy.size(self.dy)!= numpy.size(fx):
            raise RuntimeError, "SansFit: invalid error array %d <> %d" % (numpy.shape(self.dy),
                                                                           numpy.size(fx))
                                                                              
        return (self.data.y[self.idx]-fx[self.idx])/self.dy[self.idx]
    
    def get_model_distribution(self):
        """
        """
        # Compute theory data f(x)
        fx= numpy.zeros(len(self.data.x))
        fx[self.idx_unsmeared] = self.model.evalDistribution(self.data.x[self.idx_unsmeared])
       
        ## Smear theory data
        if self.smearer is not None:
            fx = self.smearer(fx, self._first_unsmeared_bin, self._last_unsmeared_bin)
                                                                                     
        return self.data.x[self.idx], fx[self.idx]
    
     
    def chi2(self, params=None):
        """
            Calculates chi^2
            @param params: dict of fit parameter values
            @return: chi^2
        """
        res = self.residuals(params)
        return numpy.sum(res*res)
     
    def fit(self):
        p = [param() for param in self.fit_params]
        out, cov_x, info, mesg, success = optimize.leastsq(self.residuals, p, full_output=1)
        return out, cov_x    
