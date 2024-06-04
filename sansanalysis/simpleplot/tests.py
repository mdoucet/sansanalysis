
import unittest
import hashlib
import random

# Import Django modules
from django.contrib.auth.models import User
from django.core.files import File

# Import SANS modules
from sans.dataloader.data_info import Data1D

# Import application modules
from sansanalysis.simpleplot.models import IqData, IqDataPoint, AnonymousSharedData, UserSharedData
import manipulations.iqdata as iqdata

TESTUSER = hashlib.md5("SANSTESTUSER1").hexdigest()
TESTFILE = "test_simpleplot_data.txt"
#TESTFILE = hashlib.md5("sphere_80.txt").hexdigest()

class iqdata_tests(unittest.TestCase):
    
    def setUp(self):
        
        # Find or create a test user
        users = User.objects.filter(username = TESTUSER)
        if len(users)==0:
            self.user = User(username=TESTUSER)
            self.user.save()
        else: 
            self.user = users[0]
        
        # Create a test data set
        data_sets = IqData.objects.filter(name = TESTFILE)
        if len(data_sets)==0:
            filename = 'simpleplot/test/sphere_80.txt'
            data = open(filename, 'r')
            content = File(data)
            self.iq_data = IqData()
            self.iq_data.owner = self.user.id
            self.iq_data.name  = TESTFILE
            self.iq_data.file.save(TESTFILE, content)    
        else: 
            self.iq_data = data_sets[0]
            
    def _create_new_iqdata(self):
        filename = 'simpleplot/test/sphere_80.txt'
        data = open(filename, 'r')
        content = File(data)
        iq_data = IqData()
        iq_data.owner = self.user.id
        iq_data.name  = TESTFILE
        iq_data.file.save(TESTFILE, content)  
        return iq_data
        
    def _create_new_user(self):
        user = User(username=str(random.random()))
        user.save()
        return user
        
    def test_fileloader(self):
        """
            Check that the file loader works
        """
        f = iqdata.FileDataLoader()
        data = f.load_file_data(self.iq_data)
        self.assertEqual(data.__class__, Data1D)
        self.assertEqual(len(data.x), 99)
        
    def test_shared_key(self):
        """
            Check that we can get and generate a shared key 
        """
        d = self._create_new_iqdata()
        self.assertEqual(iqdata.get_data_shared_key(d), None)
        self.assertEqual(iqdata.get_data_shared_key(d, create=False), None)
        self.assertNotEqual(iqdata.get_data_shared_key(d, create=True), None)
        # Now that we have created a key, this should now work
        self.assertNotEqual(iqdata.get_data_shared_key(d), None)
        
    def test_retrieve_shared_data(self):
        """
            Check that we can retrieve data from a shared key
        """
        self.assertEqual(iqdata.get_anonymous_shared_data("not a key"), None)
        key = iqdata.get_data_shared_key(self.iq_data, create=True)
        self.assertEqual(iqdata.get_anonymous_shared_data(key), self.iq_data)
        
    def test_store_shared_data(self):
        """
            Check that we can create a valid link between a user and
            a shared data set
        """
        user = self._create_new_user()
        self.assertFalse(iqdata.has_shared_data(user, self.iq_data))
        link = iqdata.create_shared_link(user, self.iq_data)
        self.assertTrue(iqdata.has_shared_data(user, self.iq_data))
        
        self.assertEqual(link.iq_data, self.iq_data)
        self.assertEqual(link.user, user)
        
    def test_deactivate_data(self):
        """
            Check that we can deactivate a data set by removing 
            the owner's ID
        """
        d = self._create_new_iqdata()
        
        # Create a link to a new user
        user = self._create_new_user()
        link = iqdata.create_shared_link(user, d)
        self.assertTrue(iqdata.has_shared_data(user, d))
        
        # Deactivate data
        self.assertEqual(d.owner, self.user.id)
        self.assertFalse(iqdata.deactivate_data(d))
        self.assertNotEqual(d.owner, self.user.id)
        self.assertEqual(d.owner, 0)
        
        # Check that the link remains
        self.assertTrue(iqdata.has_shared_data(user, d))

    def test_remove_links(self):
        """
            Check that we can remove links to a data set for a single user.
        """
        d = self._create_new_iqdata()
        
        # Create a link to a new user
        user1 = self._create_new_user()
        link = iqdata.create_shared_link(user1, d)
        self.assertTrue(iqdata.has_shared_data(user1, d))
        
        # Create a link to a new user
        user2 = self._create_new_user()
        link = iqdata.create_shared_link(user2, d)
        self.assertTrue(iqdata.has_shared_data(user2, d))  
        
        self.assertTrue(iqdata.remove_shared_link(d, user1)) 
        self.assertTrue(iqdata.has_shared_data(user2, d))  
        
        
if __name__ == '__main__':
    unittest.main()