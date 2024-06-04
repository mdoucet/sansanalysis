
# import code for encoding urls and generating md5 hashes
import urllib, hashlib

# Set your variables here
email = []
email.append("matd10@yahoo.com")
email.append("mdoucet@gmail.com")
email.append("mathieu.doucet@nist.gov")
email.append("mdoucet@utk.edu")
email.append("doucet@nist.gov")
email.append("mathieu.doucet@discoverylogic.com")

# construct the url
for item in email:
    print "\n\n"+item
    gravatar_url = "http://www.gravatar.com/avatar/"+hashlib.md5(item).hexdigest()+'?s=128&d=identicon'
    print gravatar_url
    gravatar_url = "http://www.gravatar.com/avatar/"+hashlib.md5(item).hexdigest()+'?s=128&d=monsterid'
    print gravatar_url
    gravatar_url = "http://www.gravatar.com/avatar/"+hashlib.md5(item).hexdigest()+'?s=128&d=wavatar'
    print gravatar_url
    
def test(func):
    def new_func(test, *args, **kws):

        print "hello", test
        return func(test, *args, **kws)
    return new_func

@test
def myfunc(test, yy):
    print yy
    
    

myfunc('mathieu', 'll')

import time
print time.time()