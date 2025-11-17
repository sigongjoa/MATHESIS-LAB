/**
 * Google Sign-In Button Component
 *
 * Displays a Google Sign-In button and handles OAuth callback
 * Requires: @react-oauth/google package
 */

import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import googleAuthService from '../services/googleAuthService';

interface GoogleSignInButtonProps {
  onSignInStart?: () => void;
  onSignInError?: (error: Error) => void;
  className?: string;
  buttonText?: string;
}

/**
 * GoogleSignInButton Component
 *
 * Usage:
 * import GoogleSignInButton from './components/GoogleSignInButton';
 *
 * <GoogleSignInButton
 *   onSignInStart={() => setLoading(true)}
 *   onSignInError={(error) => console.error(error)}
 *   buttonText="Google로 로그인"
 * />
 */
const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onSignInStart,
  onSignInError,
  className = '',
  buttonText = 'Google로 로그인',
}) => {
  const navigate = useNavigate();

  const handleCredentialResponse = useCallback(async (response: any) => {
    if (onSignInStart) {
      onSignInStart();
    }

    try {
      // response.credential is the JWT from Google
      const idToken = response.credential;

      if (!idToken) {
        throw new Error('No ID token received from Google');
      }

      // Verify token with backend
      const authResponse = await googleAuthService.verifyGoogleToken(idToken);

      // Store tokens
      googleAuthService.storeTokens({
        access_token: authResponse.access_token,
        refresh_token: authResponse.refresh_token,
      });

      // Redirect to dashboard/home
      navigate('/');
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown error');
      console.error('Google sign-in error:', err);
      if (onSignInError) {
        onSignInError(err);
      }
    }
  }, [navigate, onSignInStart, onSignInError]);

  React.useEffect(() => {
    // Load Google Sign-In script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);

    script.onload = () => {
      // Initialize Google Sign-In
      if (window.google) {
        const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
        if (!clientId) {
          console.error('Google Client ID is not configured. Please set REACT_APP_GOOGLE_CLIENT_ID in .env.local');
          return;
        }
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
          auto_select: false,
        });

        // Render button in container
        const buttonContainer = document.getElementById('google-signin-button');
        if (buttonContainer) {
          window.google.accounts.id.renderButton(buttonContainer, {
            theme: 'outline',
            size: 'large',
            width: '100%',
            text: 'signin_with',
          });
        }
      }
    };

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, [handleCredentialResponse]);

  return (
    <div className={className}>
      <div id="google-signin-button" style={{ display: 'flex', justifyContent: 'center' }} />
    </div>
  );
};

export default GoogleSignInButton;

// Extend window interface to include google property
declare global {
  interface Window {
    google: any;
  }
}
