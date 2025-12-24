"""Authentication module using Amazon Cognito."""

import json
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

try:
    import urllib.request
    import urllib.parse
    import urllib.error
except ImportError:
    # Fallback for different Python versions
    import urllib2 as urllib

from .config import get_config
from .exceptions import AuthenticationError, NetworkError


class AuthManager:
    """Manages authentication with Amazon Cognito."""
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.id_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.username: Optional[str] = None
    
    def _calculate_secret_hash(self, username: str) -> str:
        """Calculate the SECRET_HASH for Cognito SRP auth."""
        config = get_config()
        # Note: In production, you'd need the client secret from Cognito
        # For now, this assumes no client secret (public client)
        return ""
    
    def _make_cognito_request(self, target: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Cognito Identity Provider."""
        config = get_config()
        config.validate()
        
        url = f"https://cognito-idp.{config.aws_region}.amazonaws.com/"
        headers = {
            'Content-Type': 'application/x-amz-json-1.1',
            'X-Amz-Target': f'AWSCognitoIdentityProviderService.{target}',
        }
        
        data = json.dumps(payload).encode('utf-8')
        
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            response = urllib.request.urlopen(req, timeout=config.timeout_seconds)
            result = json.loads(response.read().decode('utf-8'))
            return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
                error_msg = error_data.get('message', str(e))
            except:
                error_msg = error_body or str(e)
            raise AuthenticationError(f"Cognito request failed: {error_msg}")
        except urllib.error.URLError as e:
            raise NetworkError(f"Network error: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def signup(self, username: str, password: str, email: str) -> None:
        """
        Sign up a new user.
        
        Args:
            username: Username for the new account
            password: Password (must meet Cognito requirements)
            email: Email address for verification
        
        Raises:
            AuthenticationError: If signup fails
        """
        config = get_config()
        config.validate()
        
        payload = {
            'ClientId': config.cognito_app_client_id,
            'Username': username,
            'Password': password,
            'UserAttributes': [
                {'Name': 'email', 'Value': email}
            ]
        }
        
        result = self._make_cognito_request('SignUp', payload)
        # Note: User may need to confirm email depending on Cognito config
    
    def login(self, username: str, password: str) -> bool:
        """
        Log in a user with username and password.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            True if login successful
        
        Raises:
            AuthenticationError: If login fails
        """
        config = get_config()
        config.validate()
        
        payload = {
            'AuthFlow': 'USER_PASSWORD_AUTH',
            'ClientId': config.cognito_app_client_id,
            'AuthParameters': {
                'USERNAME': username,
                'PASSWORD': password,
            }
        }
        
        result = self._make_cognito_request('InitiateAuth', payload)
        
        if 'AuthenticationResult' in result:
            auth_result = result['AuthenticationResult']
            self.access_token = auth_result.get('AccessToken')
            self.refresh_token = auth_result.get('RefreshToken')
            self.id_token = auth_result.get('IdToken')
            self.username = username
            
            # Calculate token expiry
            expires_in = auth_result.get('ExpiresIn', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            return True
        
        raise AuthenticationError("Login failed: No authentication result returned")
    
    def refresh_tokens(self) -> bool:
        """
        Refresh access tokens using the refresh token.
        
        Returns:
            True if refresh successful
        
        Raises:
            AuthenticationError: If refresh fails
        """
        if not self.refresh_token:
            raise AuthenticationError("No refresh token available")
        
        config = get_config()
        config.validate()
        
        payload = {
            'AuthFlow': 'REFRESH_TOKEN_AUTH',
            'ClientId': config.cognito_app_client_id,
            'AuthParameters': {
                'REFRESH_TOKEN': self.refresh_token,
            }
        }
        
        result = self._make_cognito_request('InitiateAuth', payload)
        
        if 'AuthenticationResult' in result:
            auth_result = result['AuthenticationResult']
            self.access_token = auth_result.get('AccessToken')
            self.id_token = auth_result.get('IdToken')
            
            # Calculate token expiry
            expires_in = auth_result.get('ExpiresIn', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            return True
        
        return False
    
    def logout(self) -> None:
        """Log out the current user."""
        self.access_token = None
        self.refresh_token = None
        self.id_token = None
        self.token_expiry = None
        self.username = None
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self.access_token is not None
    
    def get_access_token(self) -> str:
        """
        Get the current access token, refreshing if needed.
        
        Returns:
            Valid access token
        
        Raises:
            AuthenticationError: If not authenticated or refresh fails
        """
        if not self.is_authenticated():
            raise AuthenticationError("Not authenticated. Please log in.")
        
        # Check if token is expired or about to expire (within 5 minutes)
        if self.token_expiry:
            time_until_expiry = self.token_expiry - datetime.now()
            if time_until_expiry.total_seconds() < 300:
                # Try to refresh
                try:
                    self.refresh_tokens()
                except AuthenticationError:
                    # Refresh failed, require new login
                    self.logout()
                    raise AuthenticationError("Session expired. Please log in again.")
        
        return self.access_token


# Global auth manager instance
_auth_manager = AuthManager()


def get_auth_manager() -> AuthManager:
    """Get the global authentication manager instance."""
    return _auth_manager

