"""
Gmail API Service for AFP Project
Handles Gmail API integration using OAuth tokens from django-allauth
"""

import logging
from typing import List, Dict, Optional, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.auth.models import User
import json
import base64
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GmailService:
    """Service class for Gmail API operations"""
    
    def __init__(self, user: User):
        """Initialize Gmail service for a specific user"""
        self.user = user
        self.service = None
        self._setup_gmail_service()
    
    def _setup_gmail_service(self) -> bool:
        """Setup Gmail API service using user's OAuth tokens"""
        try:
            # Get user's Google social account
            google_account = SocialAccount.objects.filter(
                user=self.user,
                provider='google'
            ).first()
            
            if not google_account:
                logger.error(f"No Google account found for user {self.user.username}")
                return False
            
            # Get OAuth tokens
            social_token = SocialToken.objects.filter(
                account=google_account,
                app__provider='google'
            ).first()
            
            if not social_token:
                logger.error(f"No OAuth token found for user {self.user.username}")
                return False
            
            # Create credentials object
            credentials = Credentials(
                token=social_token.token,
                refresh_token=social_token.token_secret,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=social_token.app.client_id,
                client_secret=social_token.app.secret,
                scopes=['https://www.googleapis.com/auth/gmail.readonly']
            )
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.info(f"Gmail service initialized for user {self.user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Gmail service for user {self.user.username}: {str(e)}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Gmail API connection"""
        if not self.service:
            return {'success': False, 'error': 'Gmail service not initialized'}
        
        try:
            # Try to get user profile
            profile = self.service.users().getProfile(userId='me').execute()
            
            return {
                'success': True,
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal'),
                'history_id': profile.get('historyId')
            }
            
        except HttpError as e:
            logger.error(f"Gmail API test failed for user {self.user.username}: {str(e)}")
            return {
                'success': False,
                'error': f'Gmail API error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error testing Gmail for user {self.user.username}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def get_recent_messages(self, max_results: int = 50, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get recent messages from Gmail"""
        if not self.service:
            logger.error("Gmail service not initialized")
            return []
        
        try:
            # Calculate date filter (last N days)
            since_date = datetime.now() - timedelta(days=days_back)
            query = f'after:{since_date.strftime("%Y/%m/%d")}'
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info(f"No messages found for user {self.user.username}")
                return []
            
            # Get detailed message info
            detailed_messages = []
            for message in messages[:max_results]:  # Limit results
                try:
                    msg_detail = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Parse message
                    parsed_msg = self._parse_message(msg_detail)
                    if parsed_msg:
                        detailed_messages.append(parsed_msg)
                        
                except Exception as e:
                    logger.warning(f"Failed to get message {message['id']}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(detailed_messages)} messages for user {self.user.username}")
            return detailed_messages
            
        except HttpError as e:
            logger.error(f"Gmail API error getting messages for user {self.user.username}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting messages for user {self.user.username}: {str(e)}")
            return []
    
    def get_banking_messages(self, max_results: int = 100, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get messages that might be from banks"""
        if not self.service:
            logger.error("Gmail service not initialized")
            return []
        
        # Banking-related search terms
        banking_queries = [
            'from:alertas OR from:notificaciones OR from:avisos',
            'subject:transaccion OR subject:compra OR subject:retiro OR subject:transferencia',
            'subject:tarjeta OR subject:cuenta OR subject:banco',
            'body:transacción OR body:compra OR body:retiro',
            'from:banco OR from:bank'
        ]
        
        all_banking_messages = []
        
        try:
            since_date = datetime.now() - timedelta(days=days_back)
            base_query = f'after:{since_date.strftime("%Y/%m/%d")}'
            
            for banking_query in banking_queries:
                try:
                    query = f'{base_query} ({banking_query})'
                    
                    results = self.service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=max_results // len(banking_queries)
                    ).execute()
                    
                    messages = results.get('messages', [])
                    
                    for message in messages:
                        # Check if we already have this message
                        if not any(msg['id'] == message['id'] for msg in all_banking_messages):
                            try:
                                msg_detail = self.service.users().messages().get(
                                    userId='me',
                                    id=message['id'],
                                    format='full'
                                ).execute()
                                
                                parsed_msg = self._parse_message(msg_detail)
                                if parsed_msg and self._is_likely_banking_message(parsed_msg):
                                    all_banking_messages.append(parsed_msg)
                                    
                            except Exception as e:
                                logger.warning(f"Failed to get banking message {message['id']}: {str(e)}")
                                continue
                                
                except Exception as e:
                    logger.warning(f"Failed banking query '{banking_query}': {str(e)}")
                    continue
            
            # Sort by date (newest first)
            all_banking_messages.sort(key=lambda x: x['timestamp'], reverse=True)
            
            logger.info(f"Found {len(all_banking_messages)} potential banking messages for user {self.user.username}")
            return all_banking_messages[:max_results]
            
        except Exception as e:
            logger.error(f"Error getting banking messages for user {self.user.username}: {str(e)}")
            return []
    
    def _parse_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Gmail message into structured format"""
        try:
            headers = message['payload'].get('headers', [])
            
            # Extract headers
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            to = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            
            # Extract body
            body = self._extract_message_body(message['payload'])
            
            # Parse timestamp
            timestamp = datetime.fromtimestamp(int(message['internalDate']) / 1000)
            
            return {
                'id': message['id'],
                'thread_id': message['threadId'],
                'subject': subject,
                'sender': sender,
                'to': to,
                'date': date,
                'timestamp': timestamp,
                'body': body,
                'snippet': message.get('snippet', ''),
                'labels': message.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error(f"Error parsing message: {str(e)}")
            return None
    
    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        """Extract body text from message payload"""
        body = ""
        
        if payload.get('body', {}).get('data'):
            # Single part message
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif payload.get('parts'):
            # Multi-part message
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if part.get('body', {}).get('data'):
                        data = part['body']['data']
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part.get('mimeType') == 'text/html' and not body:
                    # Use HTML if no plain text found
                    if part.get('body', {}).get('data'):
                        data = part['body']['data']
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Basic HTML stripping (you might want to use a proper HTML parser)
                        body = re.sub(r'<[^>]+>', '', html_body)
        
        return body.strip()
    
    def _is_likely_banking_message(self, message: Dict[str, Any]) -> bool:
        """Determine if a message is likely from a bank"""
        # Banking keywords in Spanish and English
        banking_keywords = [
            # Spanish
            'transacción', 'transaccion', 'compra', 'retiro', 'transferencia',
            'tarjeta', 'cuenta', 'banco', 'débito', 'debito', 'crédito', 'credito',
            'saldo', 'movimiento', 'operación', 'operacion', 'cajero', 'atm',
            
            # English
            'transaction', 'purchase', 'withdrawal', 'transfer', 'card',
            'account', 'bank', 'debit', 'credit', 'balance', 'operation', 'atm'
        ]
        
        # Banking domains
        banking_domains = [
            'bancopopular.com', 'bac.cr', 'bncr.fi.cr', 'scotiabankcr.com',
            'bcr.fi.cr', 'coopeande.fi.cr', 'banco.cr', 'bancodecosta',
            'davivienda.cr', 'promerica.fi.cr'
        ]
        
        # Check sender domain
        sender_email = message.get('sender', '').lower()
        for domain in banking_domains:
            if domain in sender_email:
                return True
        
        # Check keywords in subject and body
        text_content = (message.get('subject', '') + ' ' + message.get('body', '')).lower()
        
        keyword_count = sum(1 for keyword in banking_keywords if keyword in text_content)
        
        # If we find multiple banking keywords, it's likely a banking message
        return keyword_count >= 2
    
    def get_all_emails(self, max_results: int = 200, days_back: int = 60) -> List[Dict[str, Any]]:
        """Get all emails without filtering - for manual analysis"""
        if not self.service:
            logger.error("Gmail service not initialized")
            return []
        
        try:
            # Calculate date filter (last N days)
            since_date = datetime.now() - timedelta(days=days_back)
            query = f'after:{since_date.strftime("%Y/%m/%d")}'
            
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info(f"No messages found for user {self.user.username}")
                return []
            
            # Get detailed message info
            detailed_messages = []
            for message in messages[:max_results]:  # Limit results
                try:
                    msg_detail = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Parse message
                    parsed_msg = self._parse_message(msg_detail)
                    if parsed_msg:
                        detailed_messages.append(parsed_msg)
                        
                except Exception as e:
                    logger.warning(f"Failed to get message {message['id']}: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(detailed_messages)} total messages for user {self.user.username}")
            return detailed_messages
            
        except HttpError as e:
            logger.error(f"Gmail API error getting all messages for user {self.user.username}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting all messages for user {self.user.username}: {str(e)}")
            return []

    def refresh_token_if_needed(self) -> bool:
        """Refresh OAuth token if needed"""
        # This will be handled by django-allauth token refresh
        # For now, we'll rely on the existing token management
        return True 