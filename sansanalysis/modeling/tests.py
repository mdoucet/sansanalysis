import unittest

try:
    # Running unit tests through django
    LOCAL = False
    from sansanalysis.modeling import sans_model_adapter as m
    from sansanalysis.simpleplot.models import IqData
    from sansanalysis.modeling.models import FitProblem 
    # Import Django modules
    from django.contrib.auth.models import User
    from django.core.files import File
    import forms as modeling_forms
except:
    # Running unit tests locally
    LOCAL = True
    import sans_model_adapter as m

try:
    # Running unit tests through django
    from sansanalysis.modeling import smearing_model_adapter
except:
    # Running unit tests locally
    import smearing_model_adapter


from random import random
import numpy
from scipy import optimize
from sans.dataloader.data_info import Data1D
from sans_fit import SansFit, Parameter
from sans.models.LineModel import LineModel
from sans.models import qsmearing
from sans_model_adapter import FitProblem


def sansfit(model, pars, x, y, err_y ,qmin=None, qmax=None):
    """
        Fit function
        @param model: sans model object
        @param pars: list of parameters
        @param x: vector of x data
        @param y: vector of y data
        @param err_y: vector of y errors 
    """
    if qmin==None: qmin = min(x)
    if qmax==None: qmax = max(x)
    
    def f(params):
        """
            Calculates the vector of residuals for each point 
            in y for a given set of input parameters.
            @param params: list of parameter values
            @return: vector of residuals
        """
        for i in range(len(pars)):
            pars[i].set(params[i])
        
        residuals = []
        for j in range(len(x)):
            if x[j]>=qmin and x[j]<=qmax:
                residuals.append( ( y[j] - model.runXY(x[j]) ) / err_y[j] )
        return residuals
        
    p = [param() for param in pars]
    out, cov_x, info, mesg, success = optimize.leastsq(f, p, full_output=1, warning=True)
        
    return out, cov_x 

class fit_as_list(unittest.TestCase):
    
    def setUp(self):
        x = [.5, 1.0, 1.5, 2.0, 3., 4., 5., 6., 7., 8., 9., 10., 11.]
        y = [(1+random()*.1)*i for i in range(len(x))]
        dy = [1.0]*len(x)
        self.data = Data1D(x, y, dy=dy)
        
        self.model = LineModel()
        self.fitpars = [Parameter(self.model, 'A' ,1.0), Parameter(self.model, 'B' ,1.0)]
    
    def test_sansfit(self):     
        out, cov = sansfit(self.model, self.fitpars, self.data.x, self.data.y, self.data.dy)
        
        f = SansFit(self.model, self.data, self.fitpars)
        out2, cov2 = f.fit()
        
        for i in range(2):
            self.assertAlmostEqual(out[i], out2[i], 5)
            
    def test_numpy_compatibility(self):
        """
            SansFit ensures that the data is kept in ndarray.
            In doing so, we will lose the ref to the original data
            if it was passed as a list.
        """
        f = SansFit(self.model, self.data)
        f.data.x[0] = 11111.0
        self.assertEqual(self.data.x[0], f.data.x[0])
        
    
        
class fit_tests(unittest.TestCase):
    
    def setUp(self):
        x = numpy.arange(0, 10,.5)
        y = numpy.asarray([(1+random()*.1)*i for i in range(len(x))])
        dy = numpy.ones(len(x))
        self.data = Data1D(x, y, dy=dy)
        
        self.model = LineModel()
        self.fitpars = [Parameter(self.model, 'A' ,1.0), Parameter(self.model, 'B' ,1.0)]

    def test_numpy_compatibility(self):
        """
            SansFit ensures that the data is kept in ndarray.
            In doing so, we will keep the ref to the original data
            if it was passed as an ndarray.
        """
        f = SansFit(self.model, self.data)
        f.data.x[0] = 11111.0
        self.assertEqual(self.data.x[0], f.data.x[0])      
    
    
    def test_sansfit(self):     
        out, cov = sansfit(self.model, self.fitpars, self.data.x, self.data.y, self.data.dy)
        
        f = SansFit(self.model, self.data, self.fitpars)
        out2, cov2 = f.fit()
        
        for i in range(2):
            self.assertAlmostEqual(out[i], out2[i], 5)
    
        
    def test_sansfit_with_range(self):  
        qmin = 1.0
        qmax = 8.0
        
        out, cov = sansfit(self.model, self.fitpars, self.data.x, self.data.y, self.data.dy, qmin=qmin, qmax=qmax)
        
        f = SansFit(self.model, self.data, self.fitpars, qmin=qmin, qmax=qmax)
        out2, cov2 = f.fit()
        
        for i in range(2):
            self.assertAlmostEqual(out[i], out2[i], 5)
    
    def test_chi2_call(self):

        self.model.setParam("A", 0)
        self.model.setParam("B", 0)
        
        f = SansFit(self.model, self.data)
        self.assertEqual(f.chi2(), sum(self.data.y*self.data.y))
        
    def test_chi2_dy_is_None(self):

        self.data.dy=None
        
        self.model.setParam("A", 0)
        self.model.setParam("B", 0)
        
        f = SansFit(self.model, self.data)
        self.assertEqual(f.chi2(), sum(self.data.y*self.data.y))
        
    def test_chi2_dy_is_empty_list(self):

        self.data.dy=[]
        self.model.setParam("A", 0)
        self.model.setParam("B", 0)
        
        f = SansFit(self.model, self.data)
        self.assertEqual(f.chi2(), sum(self.data.y*self.data.y))

class FitProblemTests(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_parameters(self):
        class TestClass(object):
            d = {}
            def __init__(self, d):
                self.d = d
            def process(self, d):
                for p in d:
                    self.d = d

        d = dict(a=1,b=2)
        t = TestClass(d)
        print t.d
        d['a']=3
        print t.d
        
        def switch(par):
            par = 3
        e = dict(a=1,b=2)
        print e
        switch(e['a'])
        print e

class SmearingTests(unittest.TestCase):
    def setUp(self):
        x = numpy.asarray(range(10))
        y = numpy.asarray(10*[1])
        dy = numpy.asarray(10*[1])
        self.data = Data1D(x, y, dy=dy)
        
    
    def test_from_form(self):
        if not LOCAL:
            form_pars = {'chk_scale': True, 'scale': 0.00022109129418337349, 'smear_width': 1.1, 'smear_height': 2.2, 'smearing': 3, 'chk_contrast': False, 'chk_background': False, 'q_max': 0.0055497599999999999, 'radius': 2436.7181708343446, 'background': 0.0, 'smear_type': u'Slit smearing', 'model': u'0', 'chk_radius': True, 'q_min': 0.002, 'contrast': 3.9999999999999998e-06}
            
            #smear_adapter = smearing_model_adapter.get_smear_adapter_from_dict(form_pars)
            smear_adapter = modeling_forms.get_smear_adapter_from_form_data(form_pars)
            self.assertTrue(isinstance(smear_adapter, smearing_model_adapter.SlitSmearerAdapter))
            pars = smear_adapter.get_smearing_parameters()
            self.assertTrue(type(pars)==list)
            self.assertEqual(len(pars), 2)
                                   
            smearer = smear_adapter.get_smearer(self.data)
            self.assertTrue(isinstance(smearer, qsmearing.SlitSmearer))
            self.assertEqual(smearer.width, 1.1)
            self.assertEqual(smearer.height, 2.2)
        

    def test_data_default_from_form(self):
        if not LOCAL:
            form_pars = {'chk_scale': True, 'scale': 0.00022109129418337349, 'smearing': 1, 'chk_contrast': False, 'chk_background': False, 'q_max': 0.0055497599999999999, 'radius': 2436.7181708343446, 'background': 0.0, 'smear_type': u'Point smearing', 'model': u'0', 'chk_radius': True, 'q_min': 0.002, 'contrast': 3.9999999999999998e-06}
            
            #smear_adapter = smearing_model_adapter.get_smear_adapter_from_dict(form_pars)
            smear_adapter = modeling_forms.get_smear_adapter_from_form_data(form_pars)
            self.assertTrue(isinstance(smear_adapter, smearing_model_adapter.PointSmearerAdapter))
            pars = smear_adapter.get_smearing_parameters()
            self.assertTrue(type(pars)==list)
            # In default mode, we have three summary parameters for Point Smearers
            self.assertEqual(len(pars), 3)
                            
            smearer = smear_adapter.get_smearer(self.data)
            self.assertTrue(isinstance(smearer, qsmearing.QSmearer))
            self.assertEqual(len(smearer.width), 10)
        
class FitStorageTests(unittest.TestCase):
    def setUp(self):
        if not LOCAL:
            
            # Find or create a test user
            users = User.objects.filter(username = "test_user")
            if len(users)==0:
                self.user = User(username="test_user")
                self.user.save()
            else: 
                self.user = users[0]
            
            # Create a test data set
            data_sets = IqData.objects.filter(name = "test_file")
            if len(data_sets)==0:
                filename = 'simpleplot/test/sphere_80.txt'
                data = open(filename, 'r')
                content = File(data)
                self.iq_data = IqData()
                self.iq_data.owner = self.user.id
                self.iq_data.name  = "test_file"
                self.iq_data.file.save("test_file", content)    
            else: 
                self.iq_data = data_sets[0]
            
       
    def test_storage_point_smeared(self):
        if not LOCAL:
            from data_manipulations import store_fit_problem, restore_fit_problem
            
            form_pars = {'chk_scale': True,       'scale': 0.00022109129418337349, 
                         'chk_background': False, 'background': 0.0, 
                         'chk_radius': True,      'radius': 2436.71816,                           
                         'chk_contrast': False,  'contrast': 3.99e-06,
                         'q_min': 0.002, 'q_max': 0.0055497, 
                         'model': 0, 
                         'smear_type': u'Point smearing', 
                         'smearing': 2,
                         'smear_dq': 0.115}
            
            self.fp = FitProblem(data_id=self.iq_data.id)
            modeling_forms.populate_fit_problem_from_form_data(self.fp, form_pars)

            fp_stored = store_fit_problem(self.user, self.fp)            
            fp_restored = restore_fit_problem(fp_stored.id)
            
            self.assertEqual(self.fp.data_id, fp_restored.data_id)
            self.assertEqual(self.fp.model_id, fp_restored.model_id)
            self.assertEqual(self.fp.model_name, fp_restored.model_name)
            self.assertEqual(self.fp.qmin, fp_restored.qmin)
            self.assertEqual(self.fp.qmax, fp_restored.qmax)
            self.assertEqual(self.fp.smearer_model_id, fp_restored.smearer_model_id)
            self.assertEqual(self.fp.smearer_option_id, fp_restored.smearer_option_id)
            self.assertEqual(self.fp.model_parameters, fp_restored.model_parameters)
            self.assertEqual(self.fp.chi2, fp_restored.chi2)
            self.assertEqual(self.fp.is_valid, fp_restored.is_valid)
            self.assertTrue(isinstance(fp_restored.smear_adapter, smearing_model_adapter.PointSmearerAdapter))
            self.assertEqual(self.fp.smear_adapter.get_smearing_parameters(), fp_restored.smear_adapter.get_smearing_parameters())

    def test_storage_slit_smeared(self):
        if not LOCAL:
            from data_manipulations import store_fit_problem, restore_fit_problem
            from forms import fit_problem_as_form_data
            
            form_pars = {'chk_scale': True,       'scale': 0.00022109129418337349, 
                         'chk_background': False, 'background': 0.0, 
                         'chk_radius': True,      'radius': 2436.71816,                           
                         'chk_contrast': False,  'contrast': 3.99e-06,
                         'q_min': 0.002, 'q_max': 0.0055497, 
                         'model': 0, 
                         'smear_type': u'Slit smearing', 
                         'smearing': 3,
                         'smear_width': 0.115,
                         'smear_height': 0.445}
            
            self.fp = FitProblem(data_id=self.iq_data.id)
            modeling_forms.populate_fit_problem_from_form_data(self.fp, form_pars)
            
            fp_stored = store_fit_problem(self.user, self.fp)            
            fp_restored = restore_fit_problem(fp_stored.id)
            
            self.assertEqual(self.fp.data_id, fp_restored.data_id)
            self.assertEqual(self.fp.model_id, fp_restored.model_id)
            self.assertEqual(self.fp.model_name, fp_restored.model_name)
            self.assertEqual(self.fp.qmin, fp_restored.qmin)
            self.assertEqual(self.fp.qmax, fp_restored.qmax)
            self.assertEqual(self.fp.smearer_model_id, fp_restored.smearer_model_id)
            self.assertEqual(self.fp.smearer_option_id, fp_restored.smearer_option_id)
            self.assertEqual(self.fp.model_parameters, fp_restored.model_parameters)
            self.assertEqual(self.fp.chi2, fp_restored.chi2)
            self.assertEqual(self.fp.is_valid, fp_restored.is_valid)
            self.assertTrue(isinstance(fp_restored.smear_adapter, smearing_model_adapter.SlitSmearerAdapter))
            self.assertEqual(self.fp.smear_adapter.get_smearing_parameters(), fp_restored.smear_adapter.get_smearing_parameters())

            self.assertEqual(form_pars, fit_problem_as_form_data(fp_restored))
             
            
    def test_storage_default_smeared(self):
        if not LOCAL:
            from data_manipulations import store_fit_problem, restore_fit_problem
            from forms import fit_problem_as_form_data
            
            form_pars = {'chk_scale': True,       'scale': 0.00022109129418337349, 
                         'chk_background': False, 'background': 0.0, 
                         'chk_radius': True,      'radius': 2436.71816,                           
                         'chk_contrast': False,  'contrast': 3.99e-06,
                         'q_min': 0.002, 'q_max': 0.0055497, 
                         'model': 0, 
                         'smear_type': u'Point smearing', 
                         'smearing': 1,
                         'smear_dq_max': 0.02375,
                         'smear_dq_avg': 0.00698492358804,
                         'smear_dq_min': 0.00109}
            
            self.fp = FitProblem(data_id=self.iq_data.id)
            modeling_forms.populate_fit_problem_from_form_data(self.fp, form_pars)
            
            fp_stored = store_fit_problem(self.user, self.fp)            
            fp_restored = restore_fit_problem(fp_stored.id)
            
            self.assertEqual(self.fp.data_id, fp_restored.data_id)
            self.assertEqual(self.fp.model_id, fp_restored.model_id)
            self.assertEqual(self.fp.model_name, fp_restored.model_name)
            self.assertEqual(self.fp.qmin, fp_restored.qmin)
            self.assertEqual(self.fp.qmax, fp_restored.qmax)
            self.assertEqual(self.fp.smearer_model_id, fp_restored.smearer_model_id)
            self.assertEqual(self.fp.smearer_option_id, fp_restored.smearer_option_id)
            self.assertEqual(self.fp.model_parameters, fp_restored.model_parameters)
            self.assertEqual(self.fp.chi2, fp_restored.chi2)
            self.assertEqual(self.fp.is_valid, fp_restored.is_valid)
            self.assertTrue(isinstance(fp_restored.smear_adapter, smearing_model_adapter.PointSmearerAdapter))
            self.assertEqual(self.fp.smear_adapter.get_smearing_parameters(), fp_restored.smear_adapter.get_smearing_parameters())

            self.assertEqual(form_pars, fit_problem_as_form_data(fp_restored))
             
            
            
            
class iqdata_tests(unittest.TestCase):
    
    def setUp(self):
        pass
        
            
    def test_model_list_exists(self):
        self.assertEqual(m.get_model(0)().__class__.__name__, 'SphereModel')
        self.assertEqual(m.get_model(1)().__class__.__name__, 'CylinderModel')
        
    def test_model_list_nonexistant(self):
        self.assertRaises(ValueError, m.get_model, 10000)
        
    def test_model_list_string(self):
        self.assertRaises(ValueError, m.get_model, 'sphere')

    def test_models_as_list(self):
        self.assertEqual(len(m.get_models_as_list()),len(m._models))
        
if __name__ == '__main__':
    unittest.main()