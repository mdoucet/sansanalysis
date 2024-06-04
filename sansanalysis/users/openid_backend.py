from django.contrib.auth.models import User
from sansanalysis.users.models import UserProfile
import time

class OpenIdToken:
    internal_token = True

def get_token():
    return OpenIdToken() 

class OpenIdBackend:
    """
        Provides local authentication to users that have just been
        authenticated by OpenID
    """
    def authenticate(self, username=None, password=None):
        """
            The authenticate method expects an OpenIdToken object as
            a password. This is a crude way to avoid users logging in
            through this authentication back-end by supplying their
            openid and a string. Only the application is able to
            supply a python object as a password.   
            
            @param username: the openid the user logged in with
            @param password: an OpenIdToken object
        """
        if isinstance(password, OpenIdToken):
            try:
                # Look up user by its OpenID
                profile = UserProfile.objects.get(openid=username)
                user = profile.user
            except UserProfile.DoesNotExist:
                # Create a new user. The password will always remain
                # unused when logging in through OpenID
                # The user will pick a user name during registration.
                # For now, pick a valid random user name
                user = User(username="%10.7f" % time.time())
                user.save()
                profile = UserProfile(user=user, openid=username)
                profile.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
