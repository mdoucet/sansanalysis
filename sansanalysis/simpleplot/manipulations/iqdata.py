"""
    Database manipulations to support the simpleplot application
"""
import sys, math, hashlib, time

# Import SANS modules
from sans.dataloader.loader import  Loader

# Import Django modules
from django.core.files import File

# Import application modules
from sansanalysis.simpleplot.models import IqData, IqDataPoint, AnonymousSharedData, UserSharedData
from sansanalysis.app_logging.models import store_error
import sansanalysis.settings

class FileDataLoader:
    """
    """
    errors = []
    data_info = None
    
    def has_errors(self):
        """
            Returns True if errors were found during the last load
        """
        return len(self.errors)>0
    
    def get_errors(self):
        return self.errors
    
    def load_file_data(self, iq_data):
        """
            Read data file and create associated IqDataPoint entries
            @param iq_data: IqData object
        """

        self.errors = []
        
        # Check whether we already have stored data for this set.
        # If so, delete them. To sync with the IqData table, this should
        # be done regardless of whether we can load the file or not. 
        data = IqDataPoint.objects.filter(iq_data=iq_data).order_by('x')
        for item in data:
            item.delete()
        
        # Load data from file
        try:
            #reader = ascii_reader.Reader()
            #data_info = reader.read(iq.file.path)
            data_info = Loader().load(iq_data.file.path)
            if data_info.__class__==list:
                data_info = data_info[0]
                self.errors.append("The uploaded data file has more than a single data set: only the first was loaded.")
        except:
            # Log the error and raise for the view to respond with an error page
            error_msg = "iqdata.load_file_data: error reading file %s\n%s" % (iq_data.name, sys.exc_value)
            store_error(user=None, url=None, text=error_msg, method='iqdata.load_file_data', build=sansanalysis.settings.APP_VERSION)
            self.errors.append("The uploaded data file is not in a format that can be processed.")
            return
        
        # Consistency checks for I(q) and q arrays
        if data_info.x is None or data_info.y is None:
            self.errors.append("The uploaded data has undefined Q and/or I(Q).")
            return
         
        if len(data_info.x) != len(data_info.y):
            self.errors.append("The uploaded data has different Q and I(Q) lengths.")
            return
        
        # Check whether we have errors and whether they are of the same length as I(Q)
        if data_info.dy is not None and len(data_info.dy) != len(data_info.y):
            self.errors.append("The uploaded data has different I(Q) and dI(Q) lengths.")
            return
        
        for m in [data_info.dy, data_info.dx, data_info.dxl, data_info.dxw]:
            if m is not None and len(m) != len(data_info.y):
                self.errors.append("The uploaded data has different I(Q) and dI(Q) lengths.")
                return
        
        # Check for invalid data
        for i in range(len(data_info.x)):
            if data_info.dy is not None:
                try:
                    float(data_info.dy[i])
                except:
                    data_info.dy[i]=0.0
                if data_info.dy[i]<0.0:
                    data_info.dy[i]=0.0
                    
            try:
                float(data_info.y[i])
            except:
                data_info.y[i]=0.0
                if data_info.dy is not None:
                    data_info.dy[i]=1.0
            
            try:
                float(data_info.x[i])
            except:
                self.errors.append("The uploaded data has invalid x values.")
                
        if False:
            # Store to DB
            for i in range(len(data_info.x)):
                dp = IqDataPoint(iq_data=iq_data,
                                 x=data_info.x[i], 
                                 y=data_info.y[i])
                
                if data_info.dx is not None:
                    dp.dx = data_info.dx[i]
                
                if data_info.dy is not None:
                    dp.dy = data_info.dy[i]
                
                if data_info.dxl is not None:
                    dp.dxl = data_info.dxl[i]
                
                if data_info.dxw is not None:
                    dp.dxw = data_info.dxw[i]
                
                dp.save()
                
        self.data_info = data_info
        return data_info
        

        
def get_anonymous_shared_data(key):
    """
        Retrieve IqData object by key
        @param key: shared key
    """
    shared_data = AnonymousSharedData.objects.filter(shared_key=key)
    if len(shared_data)==1:
        return shared_data[0].iq_data
    elif len(shared_data)>1:
        raise RuntimeError, "iqdata.get_anonymous_shared_data: shared_key not unique!"
    return None

def get_data_shared_key(iq, create=False):
    """
        Get a key for a given IqData object to be shared.
        @param iq: IqData object
        @param create: if True, a link will be created if none is found
    """
    keys = AnonymousSharedData.objects.filter(iq_data=iq)
    if len(keys)==0:
        if create:
            key = hashlib.md5("%s%f" % (iq.id, time.time())).hexdigest()
            key_object = AnonymousSharedData(shared_key=key, iq_data=iq)
            key_object.save()
            return key
        else:
            return None
    else: 
        return keys[0].shared_key

def create_shared_link(user, iq):
    """
        Create a UserShareData link between the user
        and a data set if it doesn't already exist
        
        Returns the link
    """
    # Verify that the link doesn't already exist
    old_shared = UserSharedData.objects.filter(iq_data=iq, user=user)
    if len(old_shared)==0:
        shared = UserSharedData(iq_data=iq, user=user)
        shared.save()
        return shared
    else:
        return old_shared[0]
    
def has_shared_data(user, iq):
    """
        Returns True if the specified user has a shared data link
        to the specified IqData object.
        @param iq: IqData object
        @param user: User object
    """
    shared = UserSharedData.objects.filter(iq_data=iq, user=user)
    return len(shared)>0

def deactivate_data(iq):
    """
        Deactivate a data set. Since many tables have IqData foreign keys, 
        we do not delete the data set. We simply change the owner to user ID = 0.
        That will prevent the data set to ever show up in the user's list of
        data and he will lose access to it.
        
        Return true if we removed shared links
    """
    iq.owner = 0
    iq.save()
    
    return False
    
def remove_shared_link(iq, user=None):
    """
        Remove all links to a data set.
        If a user is specified, remove links only for this user.
    """
    if user is None:
        shared = UserSharedData.objects.filter(iq_data=iq)
    else:
        shared = UserSharedData.objects.filter(iq_data=iq, user=user)
    
    has_links = len(shared)>0
    
    # Delete the links
    shared.delete()

    return has_links

def load_sample_data(user):
    """
        Load a sample file for the given user.
        @param user: user to associate the data to
        @return: PK of the IqData entry
    """
    # The sample file from the test folder
    filename = sansanalysis.settings.SAMPLE_LOCATION+'sphere_80.txt'
    data = open(filename, 'r')
    content = File(data)
    iq = IqData()
    iq.owner = user.id
    iq.name  = 'sample_data.txt'
    iq.file.save('sample_data.txt', content)  
    return iq.id
