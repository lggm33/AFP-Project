from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for AFP project"""
    
    def get_login_redirect_url(self, request):
        """Redirect to our Django success handler which will generate tokens"""
        return 'http://127.0.0.1:8000/auth/success/'


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter to handle existing users"""
    
    def pre_social_login(self, request, sociallogin):
        """
        This method is called when a user is logging in via a social provider.
        If a user exists with the same email, connect the social account to that user.
        """
        if sociallogin.is_existing:
            return
        
        # Check if a user with this email already exists
        if sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email')
            if email:
                try:
                    existing_user = User.objects.get(email=email)
                    # Connect this social account to the existing user
                    sociallogin.connect(request, existing_user)
                except User.DoesNotExist:
                    pass
    
    def get_connect_redirect_url(self, request, socialaccount):
        """Redirect to our Django success handler after connecting social account"""
        return 'http://127.0.0.1:8000/auth/success/'
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle authentication errors by redirecting to frontend"""
        return HttpResponseRedirect('http://localhost:3000/login?error=auth_failed') 