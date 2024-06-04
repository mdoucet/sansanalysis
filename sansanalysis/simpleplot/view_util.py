# Python imports
import sys, math

# Django imports
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.db.models import Q

# Application imports
from sansanalysis.simpleplot.models import IqData, UserSharedData
from sansanalysis.simpleplot.models import RecentData, PrInversion, UserSharedPr
from sansanalysis.app_logging.models import store_error
from sansanalysis.modeling.models import FitProblem
import sansanalysis.settings

# Data manipulations
import manipulations.iqdata
import manipulations.prdata

DATA_SCALE_X_QSTRING = 'scale_x'
DATA_SCALE_Y_QSTRING = 'scale_y'
OUTPUT_SCALE_X_QSTRING = 'out_scale_x'
OUTPUT_SCALE_Y_QSTRING = 'out_scale_y'

def dashboard_response():
    return HttpResponseRedirect(reverse('sansanalysis.simpleplot.views.select_data'))

def get_recent_data_by_user(user_id):
    """
        Get latest five data sets visited by the user
        
        @param user_id: user id
    """
    data = RecentData.objects.filter(user_id=user_id).order_by('visited_on').reverse()
    user = User.objects.get(pk=user_id)   
    data_names = []
    recent     = []
    for item in data:
        if (item.iq_data.owner == user_id or manipulations.iqdata.has_shared_data(user, item.iq_data)) \
            and item.iq_data.name not in data_names and len(data_names)<5:
            data_names.append(item.iq_data.name)
            recent.append({'name':item.iq_data.name,
                           'url':reverse('sansanalysis.simpleplot.views.data_details', args=(item.iq_data.id,))})
                          
    return recent

def get_recent_prfits_by_user(user_id):
    """
        Get latest five data sets visited by the user
        
        Make sure that all links are available and that the user
        is either the owner of the file or has access through
        a stored link.
        
        @param user_id: user id
    """
    data = PrInversion.objects.filter(user_id=user_id).order_by('created_on').reverse()
    user = User.objects.get(pk=user_id)        
        
    recent = []
    labels = []
    for item in data:
        # Check that the user is the owner or has stored a link to that data
        if (item.iq_data.owner == user_id or manipulations.iqdata.has_shared_data(user, item.iq_data)) \
            and item.iq_data.name not in labels and len(recent)<5:
            labels.append(item.iq_data.name)
            recent.append({'name': "P(r): %s" % item.iq_data.name,
                           'time': item.created_on,
                           'url':reverse('sansanalysis.simpleplot.views.invert', args=(item.iq_data.id,))})
    return recent
          
def get_recent_prfits_by_iqdata(user_id, iq_id):
    """
        Get latest five data sets visited by the user
        
        Make sure that all links are available and that the user
        is either the owner of the file or has access through
        a stored link.
        
        @param user_id: user id
    """
    chi2_query = 'SELECT chi2 FROM simpleplot_proutput WHERE simpleplot_prinversion.id=simpleplot_proutput.inversion_id'
    data = PrInversion.objects.filter(user_id=user_id, iq_data__id=iq_id).extra(
                select={'chi2': chi2_query}).order_by('created_on').reverse()
    user = User.objects.get(pk=user_id)         
        
    recent = []
    labels = []
    for item in data:
        label = "P(r): D=%-5.4g; &chi;<span class='exponent'> 2</span>=%-3.2g" % (item.d_max, item.chi2)
        if (item.iq_data.owner == user_id or manipulations.iqdata.has_shared_data(user, item.iq_data)) \
            and label not in labels and len(recent)<5:
            labels.append(label)
            recent.append({'name':label,
                           'time': item.created_on,
                           'url':reverse('sansanalysis.simpleplot.views.invert', args=(item.iq_data.id,
                                                                                   item.id,))})            
    return recent
          
          
class BaseSorter(object):
    """
        Sorter object to organize data in a sorted grid
    """
    ## Sort item query string
    SORT_ITEM_QUERY_STRING = 'ds'
    ## Sort direction query string
    SORT_DIRECTION_QUERY_STRING = 'dd'
    ## Query string to get the full list as opposed to only the top items
    FULL_LIST_QUERY_STRING = 'da'
    ## Number of top items
    N_TOP = 5
    
    # Sort direction information
    KEY_ASC     = 'asc'
    KEY_DESC    = 'desc'
    DEFAULT_DIR = KEY_ASC
    DIR_CHOICES = [KEY_ASC, KEY_DESC]
    
    # Sort item
    KEY_MOD     = 'modified'
    KEY_NAME    = 'name'
    KEY_OWNER   = 'owner'
    DEFAULT_ITEM = KEY_MOD
    ITEM_CHOICES = [KEY_MOD, KEY_NAME, KEY_OWNER]
    COLUMN_DICT = {KEY_MOD: 'modified_on',
                   KEY_NAME: 'name',
                   KEY_OWNER: 'owner'}
    
    
    def __init__(self, request):
        """
            Initialize the sorting parameters
            @param request: get the sorting information from the HTTP request
        """
        # Get the default from the user session
        default_dir = request.session.get(self.SORT_DIRECTION_QUERY_STRING, default=self.DEFAULT_DIR)
        default_item = request.session.get(self.SORT_ITEM_QUERY_STRING, default=self.DEFAULT_ITEM)
        
        # Get the sorting options from the query parameters
        self.sort_dir = request.GET.get(self.SORT_DIRECTION_QUERY_STRING, default_dir)
        self.sort_key = request.GET.get(self.SORT_ITEM_QUERY_STRING, default_item)
        
        # Clean up sort direction
        self.sort_dir = self.sort_dir.lower().strip()
        if self.sort_dir not in self.DIR_CHOICES:
            self.sort_dir = self.DEFAULT_DIR
        
        # Clean up sort column
        self.sort_key = self.sort_key.lower().strip()
        if self.sort_key not in self.ITEM_CHOICES:
            self.sort_key = self.DEFAULT_ITEM        
        self.sort_item = self.COLUMN_DICT[self.sort_key]
        
        # Store sorting parameters in session
        request.session[self.SORT_DIRECTION_QUERY_STRING] = self.sort_dir
        request.session[self.SORT_ITEM_QUERY_STRING] = self.sort_item
        
        ## User ID
        self.user = request.user
        
        ## Get the full-list query key if it exists
        self.full_list = True if request.GET.get(self.FULL_LIST_QUERY_STRING, default=None) is not None else False

    def _create_header_dict(self, long_name, url_name):
        """
            Creates column header, the following classes have to
            be define in the CSS style sheet

            "sorted descending"
            "sorted ascending"
            
            @param long_name: name that will appear in the table header
            @param url_name: URL query field
        """
        d = {'name': long_name,
             'url':"?%s=%s&amp;%s=%s" % (self.SORT_DIRECTION_QUERY_STRING,
                                         self.KEY_ASC, self.SORT_ITEM_QUERY_STRING, url_name)}
        if self.sort_key == url_name:
            if self.sort_dir == self.KEY_DESC:
                d['class'] = "sorted descending"
            else:
                d['class'] = "sorted ascending"
                d['url'] = "?%s=%s&amp;%s=%s" % (self.SORT_DIRECTION_QUERY_STRING, 
                                                 self.KEY_DESC, self.SORT_ITEM_QUERY_STRING, url_name)
        return d
            
    def __call__(self):
        """
            Returns the data and header to populate a data grid
        """
        # Query the database
        data = self._retrieve_data()
        get_all_url = self._get_all_url(len(data))
            
        # Check whether we want the full list or not
        if not self.full_list:
            data = data[0:self.N_TOP]
        
        # Create the data dictionary
        user_data = []
        for datum in data:
            d = {'name':datum.name, 
                 'owner':datum.get_user_name(),
                 'modified':datum.modified_on,
                 'delete_url':reverse('sansanalysis.simpleplot.views.delete_data', args=(datum.id,)),
                 'url':reverse('sansanalysis.simpleplot.views.data_details', args=(datum.id,))}
            user_data.append(d)
            
        # Create the header dictionary    
        header = []
        header.append(self._create_header_dict("File name", self.KEY_NAME))
        header.append(self._create_header_dict("Owner", self.KEY_OWNER))
        header.append(self._create_header_dict("Modified on", self.KEY_MOD))
        #header.append({'class': ""})
        
        return user_data, header, get_all_url
    
    def _retrieve_data(self): return NotImplemented

    def _get_all_url(self, datalen):
        """
            Returns the url with the query string to get all items
        """
        if self.full_list or datalen<=self.N_TOP:
            return None
        else:
            return reverse('sansanalysis.simpleplot.views.select_data')+'?%s=1' % self.FULL_LIST_QUERY_STRING
    
class DataSorter(BaseSorter):
    
    ## Sort item query string
    SORT_ITEM_QUERY_STRING = 'ds'
    ## Sort direction query string
    SORT_DIRECTION_QUERY_STRING = 'dd'
    ## Query string to get the full list as opposed to only the top 5
    FULL_LIST_QUERY_STRING = 'da'
    
    def _retrieve_data(self):
        """
            Return the IqData owned by the user
        """
        # Query the database
        if self.sort_dir==self.KEY_DESC:
            return IqData.objects.filter(Q(owner=self.user.id) | Q(usershareddata__user=self.user)).order_by(self.sort_item).reverse()
        else:
            return IqData.objects.filter(Q(owner=self.user.id) | Q(usershareddata__user=self.user)).order_by(self.sort_item)
            
class BasePrSorter(BaseSorter):
    """
        Sorter object to organize data in a sorted grid
    """
    ## Sort item query string
    SORT_ITEM_QUERY_STRING = 'ps'
    ## Sort direction query string
    SORT_DIRECTION_QUERY_STRING = 'pd'
    ## Query string to get the full list as opposed to only the top 5
    FULL_LIST_QUERY_STRING = 'pa'
    
    # Sort item
    KEY_DMAX    = 'd_max'
    KEY_NAME    = 'name'
    KEY_CREATED = 'created'
    KEY_QMIN    = 'qmin'
    KEY_QMAX    = 'qmax'
    KEY_CHI2    = 'chi2'
    KEY_OWNER   = 'owner'
    DEFAULT_ITEM = KEY_CREATED
    ITEM_CHOICES = [KEY_NAME, KEY_DMAX, KEY_QMIN, KEY_QMAX, KEY_CHI2, KEY_CREATED, KEY_OWNER]
    COLUMN_DICT = {KEY_DMAX: 'd_max',
                   KEY_NAME: 'iq_data__name',
                   KEY_QMIN: 'q_min',
                   KEY_QMAX: 'q_max',
                   KEY_CHI2: 'chi2',
                   KEY_OWNER: 'user_id',
                   KEY_CREATED: 'created_on'}
            
    def __call__(self):
        """
            Returns the data and header to populate a data grid
        """
        # Query the database
        data = self._retrieve_data()
        if data is None:
            return None, None, None
        
        # Create the data dictionary
        user_data = []
        count = 0
        for datum in data:
            # Check that the user has access to the data
            if (self.user.id == datum.iq_data.owner \
            or (self.user.is_authenticated() and manipulations.iqdata.has_shared_data(self.user, datum.iq_data))):
                if (self.full_list or len(user_data)<self.N_TOP):
                    d = {'name':datum.iq_data.name, 
                         'd_max':datum.d_max, 
                         'q_min':datum.q_min, 
                         'q_max':datum.q_max, 
                         'owner':datum.get_user_name(),
                         'modified':datum.created_on,
                         'chi2': "%3.2g" % datum.chi2,
                         'delete_url':reverse('sansanalysis.simpleplot.views.delete_pr', args=(datum.iq_data.id, datum.id,)),
                         'url':reverse('sansanalysis.simpleplot.views.invert', args=(datum.iq_data.id, datum.id,))}
                    user_data.append(d)
                count += 1
            
        # Create the header dictionary    
        header = []
        header.append(self._create_header_dict("File name", self.KEY_NAME))
        header.append(self._create_header_dict("Owner", self.KEY_OWNER))
        header.append(self._create_header_dict("D<span class='subscript'>max</span> [&Aring;]", self.KEY_DMAX))
        header.append(self._create_header_dict("Q<span class='subscript'>min</span> [1/&Aring;]", self.KEY_QMIN))
        header.append(self._create_header_dict("Q<span class='subscript'>max</span> [1/&Aring;]", self.KEY_QMAX))
        header.append(self._create_header_dict("Chi <span class='exponent'>2</span>", self.KEY_CHI2))
        header.append(self._create_header_dict("Created on", self.KEY_CREATED))
        
        return user_data, header, self._get_all_url(count)
    
    def _retrieve_data(self):
        """
            Return the shared IqData accessible by the user
        """
        # Chi2 query
        chi2_query = 'SELECT chi2 FROM simpleplot_proutput WHERE simpleplot_prinversion.id=simpleplot_proutput.inversion_id'
        # Query the database
        if self.sort_dir==self.KEY_DESC:
            return PrInversion.objects.filter(Q(user_id=self.user.id)|Q(usersharedpr__user=self.user)).extra(
                select={'chi2': chi2_query}).order_by(self.sort_item).reverse()
        else:
            return PrInversion.objects.filter(Q(user_id=self.user.id)|Q(usersharedpr__user=self.user)).extra(
                select={'chi2': chi2_query}).order_by(self.sort_item)


class ModelFitSorter(BaseSorter):
    """
        Sorter object to organize data in a sorted grid
    """
    ## Sort item query string
    SORT_ITEM_QUERY_STRING = 'fs'
    ## Sort direction query string
    SORT_DIRECTION_QUERY_STRING = 'fd'
    ## Query string to get the full list as opposed to only the top 5
    FULL_LIST_QUERY_STRING = 'fa'
        
    # Sort item
    KEY_MODEL   = 'model'
    KEY_DATA    = 'data'
    KEY_CREATED = 'created'
    KEY_QMIN    = 'qmin'
    KEY_QMAX    = 'qmax'
    KEY_CHI2    = 'chi2'
    KEY_OWNER   = 'owner'
    KEY_SMEAR   = 'smear'
    DEFAULT_ITEM = KEY_CREATED
    ITEM_CHOICES = [KEY_DATA, KEY_MODEL, KEY_SMEAR, KEY_QMIN, KEY_QMAX, KEY_CHI2, KEY_CREATED, KEY_OWNER]
    COLUMN_DICT = {KEY_MODEL: 'model__name',
                   KEY_DATA: 'iq_data__name',
                   KEY_SMEAR: 'smearing_model__model_info__name',
                   KEY_QMIN: 'q_min',
                   KEY_QMAX: 'q_max',
                   KEY_CHI2: 'chi2',
                   KEY_OWNER: 'owner__id',
                   KEY_CREATED: 'created_on'}
            
    def __call__(self):
        """
            Returns the data and header to populate a data grid
        """
        # Query the database
        data = self._retrieve_data()
        if data is None:
            return None, None, None
        
        # Create the data dictionary
        user_data = []
        count = 0
        for datum in data:
            smear = "None" if datum.smearing_model is None else datum.smearing_model.model_info.name
            # Check that the user has access to the data
            if (self.user.id == datum.iq_data.owner \
            or (self.user.is_authenticated() and manipulations.iqdata.has_shared_data(self.user, datum.iq_data))):
                if (self.full_list or len(user_data)<self.N_TOP):
                    d = {'data':datum.iq_data.name, 
                         'model':datum.model.name,
                         'smear': smear, 
                         'q_min':datum.q_min, 
                         'q_max':datum.q_max, 
                         'owner':datum.get_user_name(),
                         'modified':datum.created_on,
                         'chi2': "%3.2g" % datum.chi2,
                         'delete_url':reverse('sansanalysis.modeling.views.delete_fit', args=(datum.iq_data.id, datum.id,)),
                         'url':reverse('sansanalysis.modeling.views.fit', args=(datum.iq_data.id, datum.id,))}
                    user_data.append(d)
                count += 1
            
        # Create the header dictionary    
        header = []
        header.append(self._create_header_dict("File name", self.KEY_DATA))
        header.append(self._create_header_dict("Model name", self.KEY_MODEL))
        header.append(self._create_header_dict("Smearing", self.KEY_SMEAR))
        header.append(self._create_header_dict("Owner", self.KEY_OWNER))
        header.append(self._create_header_dict("Q<span class='subscript'>min</span> [1/&Aring;]", self.KEY_QMIN))
        header.append(self._create_header_dict("Q<span class='subscript'>max</span> [1/&Aring;]", self.KEY_QMAX))
        header.append(self._create_header_dict("Chi <span class='exponent'>2</span>", self.KEY_CHI2))
        header.append(self._create_header_dict("Created on", self.KEY_CREATED))
        
        return user_data, header, self._get_all_url(count)
    
    def _retrieve_data(self):
        """
            Return the shared IqData accessible by the user
        """
        # Query the database
        if self.sort_dir==self.KEY_DESC:
            return FitProblem.objects.filter(Q(owner__id=self.user.id)|Q(usersharedfit__user=self.user)).order_by(self.sort_item).reverse()
            #return FitProblem.objects.filter(Q(owner__id=self.user.id)).order_by(self.sort_item).reverse()
        else:
            return FitProblem.objects.filter(Q(owner__id=self.user.id)|Q(usersharedfit__user=self.user)).order_by(self.sort_item)
            #return FitProblem.objects.filter(Q(owner__id=self.user.id)).order_by(self.sort_item)




def get_plot_data(plot_data, scale_x='linear', scale_y='linear'):
    """
        Get the information needed to plot I(q)
        
    """
    # Check that a data set is available
    # Get the data information to be displayed
    iq_data = []
    ticks_y = None
    ticks_x = None
    
    if plot_data is None:
        return iq_data, ticks_x, ticks_y

    def _get_ticks(axis, protect=False):
        _ticks = []
        try:
            y_raw = [ y for y in plot_data[axis] if y>0 ]

            if protect and len(y_raw)==0:
                return str([-0.1,0.1])
            
            min_y = int(math.floor(math.log10(min(y_raw))))
            max_y = int(math.ceil(math.log10(max(y_raw))))
            if max_y==min_y:
                max_y = min_y + 1
            n_ticks = int(math.ceil((max_y-min_y)/5.0))
            for i in range(min_y, max_y, n_ticks):
                value = 1.0+i*1.0
                _ticks.append([value, "%g" % math.pow(10,value)])
        except:
            # Log the error and raise for the view to respond with an error page
            error_msg = "Error scaling %s data\n%s" % (axis, sys.exc_value)
            store_error(user=None, url=None, text=error_msg, method='view_util.get_plot_data', build=sansanalysis.settings.APP_VERSION)
            raise
                               
        return str(_ticks)


    # Read the requested data, and check it.
    try:
        err_min = [0]*len(plot_data['x'])
        err_max = [0]*len(plot_data['x'])        
        if plot_data['dy'] is not None and len(plot_data['x']) == len(plot_data['dy']):
            for i in range(len(plot_data['x'])):
                if scale_y=='linear':
                    err_min[i] = plot_data['dy'][i]
                    err_max[i] = plot_data['dy'][i]
                elif scale_y=='log':
                    value = float(plot_data['y'][i])
                    if value>0:
                        delta = float(plot_data['dy'][i])
                        value_min = value-delta
                        value_max = value+delta
                        if value_min>0: err_min[i] = math.log(value)-math.log(value_min)
                        else: err_min[i] = math.log(value)
                        if value_max>0: err_max[i] = math.log(value_max)-math.log(value)
    except:
        # Log the error and raise for the view to respond with an error page
        error_msg = "Error processing error bars\n%s" % sys.exc_value
        store_error(user=None, url=None, text=error_msg, method='view_util.get_plot_data', build=sansanalysis.settings.APP_VERSION)
        
        
    try:                    
        if scale_x=='linear' and scale_y=='linear':            
            iq_data = [ [plot_data['x'][i], plot_data['y'][i], 0, err_min[i], err_max[i] ] for i in range(len(plot_data['x'])) ]
        
        elif scale_x=='linear' and scale_y=='log':
            iq_data = [ [plot_data['x'][i], math.log10(float(plot_data['y'][i])), 0, err_min[i], err_max[i] ] for i in range(len(plot_data['x'])) if float(plot_data['y'][i])>0 ]
            ticks_y = _get_ticks('y', protect=True)
        
        elif scale_x=='log' and scale_y=='linear':
            iq_data = [ [math.log10(float(plot_data['x'][i])), plot_data['y'][i], 0, err_min[i], err_max[i] ] for i in range(len(plot_data['x'])) if float(plot_data['y'][i])>0 ]
            ticks_x = _get_ticks('x')
        
        elif scale_x=='log' and scale_y=='log':
            iq_data = [ [math.log10(float(plot_data['x'][i])), math.log10(float(plot_data['y'][i])), 0, err_min[i], err_max[i] ] for i in range(len(plot_data['x'])) if float(plot_data['y'][i])>0 ]
            ticks_y = _get_ticks('y', protect=True)
            ticks_x = _get_ticks('x')

    except:
        # Log the error and raise for the view to respond with an error page
        error_msg = "Error reading file\n%s" % sys.exc_value
        store_error(user=None, url=None, text=error_msg, method='view_util.get_plot_data', build=sansanalysis.settings.APP_VERSION)
        raise

    return iq_data, ticks_x, ticks_y

def get_iq_data_dict(request, iq):
    session_iq = request.session.get('iq', default=None)
    
    # Errors not fully implemented
    errors = []
    
    if session_iq is None or \
        (not session_iq.has_key('iq_id')) or \
        session_iq['iq_id']!=iq.id:
        
        #errors.append("Data was loaded [remove this]")
        # Load data from file
        loader = manipulations.iqdata.FileDataLoader()
        data_info = loader.load_file_data(iq)
        if data_info is None:
            error_msg = "Could not read file [iq_id=%s]" % str(iq.id)
            store_error(user=None, url=None, text=error_msg, method='view_util.get_plottable_iq', build=sansanalysis.settings.APP_VERSION)
            raise RuntimeError, "Data loader could not read the data file [ID=%s]." % str(iq.id)
        
        # Check for loading errors
        if loader.has_errors():
            errors.extend(loader.get_errors())
    
        # Store session data
        session_iq = {'iq_id':iq.id,
                      'x':data_info.x,
                      'y':data_info.y,
                      'dy':data_info.dy}
        request.session['iq'] = session_iq
    
    return session_iq, errors


def get_qrange_iq(request, iq):
    """
        Return the Q range for a given data set
        
        #TODO: this should be a DB query. We should have this stored as meta data.
    """
    session_iq, errors = get_iq_data_dict(request, iq)
    return min(session_iq['x']), max(session_iq['x'])



def get_plottable_iq(request, iq):
    
    session_iq, errors = get_iq_data_dict(request, iq)
    
    scale_x = request.session.get(DATA_SCALE_X_QSTRING, default='linear')
    scale_y = request.session.get(DATA_SCALE_Y_QSTRING, default='linear')
    iq_data, ticks_x, ticks_y = get_plot_data(session_iq, scale_x, scale_y)
    
    return  iq_data, ticks_x, ticks_y, errors


def has_shared_data_info(request, iq):
    """
        Checks whether the user has the correct shared key for a given data set stored in the session.
    """
    return (request.session.get('data_shared_key', default=None) != None \
            and request.session.get('data_shared_key').has_key(iq.id) \
            and request.session.get('data_shared_key')[iq.id] == manipulations.iqdata.get_data_shared_key(iq.id))

def get_shared_data_key(request, iq_id):
    """
        Checks whether the user has the correct shared key for a given data set stored in the session,
        if so return the key.
        
        @param iq_id: PK of IqData object
    """
    # The IDs are stored as integer
    if (request.session.get('data_shared_key', default=None) != None \
        and request.session.get('data_shared_key').has_key(iq_id) \
        and request.session.get('data_shared_key')[iq_id] == manipulations.iqdata.get_data_shared_key(iq_id)):
        return request.session.get('data_shared_key')[iq_id]
    return None

def get_shared_pr_key(request, pr_id):
    """
        Checks whether the user has the correct shared key for a given pr inversion stored in the session,
        if so return the key.
        
        @param pr_id: PK of PrInversion object
    """
    if (request.session.get('pr_shared_key', default=None) != None \
        and request.session.get('pr_shared_key').has_key(pr_id) \
        and request.session.get('pr_shared_key')[pr_id] == manipulations.prdata.get_pr_shared_key(pr_id)):
        return request.session.get('pr_shared_key')[pr_id]
    return None


