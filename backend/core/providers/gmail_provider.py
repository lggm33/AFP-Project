"""
Gmail Provider for AFP Project
Implements BaseEmailProvider using Integration model for OAuth tokens
"""

import logging
from typing import List, Dict, Optional, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import base64
import re
from rest_framework import status
from .base_provider import BaseEmailProvider

logger = logging.getLogger(__name__)

class GmailProvider(BaseEmailProvider):
    """Gmail implementation of BaseEmailProvider"""
    
    def __init__(self, integration):
        """Initialize Gmail provider with integration"""
        super().__init__(integration)
        self.service = None
        self._setup_gmail_service()
    
    def _setup_gmail_service(self) -> bool:
        """Setup Gmail API service using OAuth tokens from Integration"""
        try:
            oauth_tokens = self.get_oauth_tokens()
            
            if not oauth_tokens:
                logger.error(f"No OAuth tokens found for integration {self.integration.id}")
                return False
            
            # Create credentials object from Integration tokens
            credentials = Credentials(
                token=oauth_tokens.get('access_token'),
                refresh_token=oauth_tokens.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=oauth_tokens.get('client_id'),
                client_secret=oauth_tokens.get('client_secret'),
                scopes=['https://www.googleapis.com/auth/gmail.readonly']
            )
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.info(f"Gmail service initialized for integration {self.integration.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Gmail service for integration {self.integration.id}: {str(e)}")
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
                'history_id': profile.get('historyId'),
                'integration_id': self.integration.id
            }
            
        except HttpError as e:
            logger.error(f"Gmail API test failed for integration {self.integration.id}: {str(e)}")
            return {
                'success': False,
                'error': f'Gmail API error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error testing Gmail for integration {self.integration.id}: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def get_all_messages(self, days_back: int = 30, sender_filter: str = None, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get all messages from Gmail within specified days with pagination"""
        if not self.service:
            logger.error("Gmail service not initialized")
            return {
                'error': 'Gmail service not initialized',
                'success': False
            }
        
        try:
            # Calculate date filter for exact days back
            since_date = datetime.now() - timedelta(days=days_back)
            until_date = datetime.now()
            
            # Build query for date range
            query_parts = [
                f'after:{since_date.strftime("%Y/%m/%d")}',
                f'before:{until_date.strftime("%Y/%m/%d")}'
            ]
            
            # Add sender filter if provided
            if sender_filter:
                if '|' in sender_filter:
                    # Multiple senders (OR logic)
                    sender_emails = sender_filter.split('|')
                    sender_query = ' OR '.join([f'from:{email.strip()}' for email in sender_emails])
                    query_parts.append(f'({sender_query})')
                else:
                    # Single sender or domain
                    query_parts.append(f'from:{sender_filter}')
            
            query = ' '.join(query_parts)
            logger.info(f"Gmail query: {query}")
            
            # STEP 1: Get ALL message IDs first (lightweight operation)
            all_message_ids = []
            next_page_token = None
            
            logger.info(f"Fetching all message IDs for the last {days_back} days...")
            
            while True:
                list_params = {
                    'userId': 'me',
                    'q': query,
                    'maxResults': 500  # Gmail API max per request
                }
                
                if next_page_token:
                    list_params['pageToken'] = next_page_token
                
                results = self.service.users().messages().list(**list_params).execute()
                messages = results.get('messages', [])
                
                if not messages:
                    break
                
                # Just collect message IDs
                all_message_ids.extend([msg['id'] for msg in messages])
                
                # Check if there are more pages
                next_page_token = results.get('nextPageToken')
                if not next_page_token:
                    break
            
            total_count = len(all_message_ids)
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
            
            logger.info(f"Found {total_count} total messages, {total_pages} pages with {page_size} per page")
            
            # STEP 2: Calculate pagination
            start_index = (page - 1) * page_size
            end_index = min(start_index + page_size, total_count)
            
            if start_index >= total_count:
                # Page out of range
                return {
                    'messages': [],
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': False,
                    'has_previous': page > 1
                }
            
            # STEP 3: Get detailed info for messages in current page
            page_message_ids = all_message_ids[start_index:end_index]
            detailed_messages = []
            
            logger.info(f"Fetching details for page {page} ({len(page_message_ids)} messages)")
            
            for msg_id in page_message_ids:
                try:
                    msg_detail = self.service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='full'
                    ).execute()
                    
                    # Parse message
                    parsed_msg = self._parse_message(msg_detail)
                    if parsed_msg:
                        parsed_msg['integration_id'] = self.integration.id
                        detailed_messages.append(parsed_msg)
                        
                except Exception as e:
                    logger.warning(f"Failed to get message {msg_id}: {str(e)}")
                    continue
            
            # Sort by date (newest first)
            detailed_messages.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # STEP 4: Return paginated result
            result = {
                'messages': detailed_messages,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
                'date_range': {
                    'start': since_date.isoformat(),
                    'end': until_date.isoformat(),
                    'days_back': days_back
                }
            }
            
            logger.info(f"Returning page {page}/{total_pages} with {len(detailed_messages)} messages")
            return result
            
        except HttpError as e:
            logger.error(f"Gmail API error getting messages for integration {self.integration.id}: {str(e)}")
            return {
                'messages': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'has_next': False,
                'has_previous': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting messages for integration {self.integration.id}: {str(e)}")
            return {
                'messages': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'has_next': False,
                'has_previous': False,
                'error': str(e)
            }
    
    def get_banking_messages(self, days_back: int = 30, user_bank_senders: List[str] = None, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get messages from user's configured bank senders with pagination"""
        if not self.service:
            logger.error("Gmail service not initialized")
            return {
                'error': 'Gmail service not initialized',
                'success': False,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
            
        
        # If no user bank senders provided, return error
        if not user_bank_senders:
            logger.warning(f"No bank senders provided for integration {self.integration.id}")
            return {
                'error': 'No bank senders configured',
                'success': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
            }
        
        try:
            # Calculate date filter for exact days back
            since_date = datetime.now() - timedelta(days=days_back)
            until_date = datetime.now()
            
            # Build query with user's bank senders
            date_query = f'after:{since_date.strftime("%Y/%m/%d")} before:{until_date.strftime("%Y/%m/%d")}'
            
            # Create sender filter from user's bank senders
            sender_queries = [f'from:{sender}' for sender in user_bank_senders]
            sender_query = ' OR '.join(sender_queries)
            
            query = f'{date_query} ({sender_query})'
            logger.info(f"Banking messages query: {query}")
            
            # STEP 1: Get ALL message IDs first (lightweight operation)
            all_message_ids = []
            next_page_token = None
            
            logger.info(f"Fetching all banking message IDs for the last {days_back} days...")
            
            while True:
                list_params = {
                    'userId': 'me',
                    'q': query,
                    'maxResults': 500  # Gmail API max per request
                }
                
                if next_page_token:
                    list_params['pageToken'] = next_page_token
                
                results = self.service.users().messages().list(**list_params).execute()
                messages = results.get('messages', [])
                
                if not messages:
                    break
                
                # Just collect message IDs
                all_message_ids.extend([msg['id'] for msg in messages])
                
                # Check if there are more pages
                next_page_token = results.get('nextPageToken')
                if not next_page_token:
                    break
            
            total_count = len(all_message_ids)
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
            
            logger.info(f"Found {total_count} total banking messages, {total_pages} pages with {page_size} per page")
            
            # STEP 2: Calculate pagination
            start_index = (page - 1) * page_size
            end_index = min(start_index + page_size, total_count)
            
            if start_index >= total_count:
                # Page out of range
                return {
                    'messages': [],
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': False,
                    'has_previous': page > 1
                }
            
            # STEP 3: Get detailed info for messages in current page
            page_message_ids = all_message_ids[start_index:end_index]
            detailed_messages = []
            
            logger.info(f"Fetching details for banking page {page} ({len(page_message_ids)} messages)")
            
            for msg_id in page_message_ids:
                try:
                    msg_detail = self.service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='full'
                    ).execute()
                    
                    parsed_msg = self._parse_message(msg_detail)
                    if parsed_msg:
                        # Verify sender matches one of the user's bank senders
                        sender_email = parsed_msg.get('sender', '').lower()
                        if any(bank_sender.lower() in sender_email for bank_sender in user_bank_senders):
                            parsed_msg['integration_id'] = self.integration.id
                            detailed_messages.append(parsed_msg)
                            
                except Exception as e:
                    logger.warning(f"Failed to get banking message {msg_id}: {str(e)}")
                    continue
            
            # Sort by date (newest first)
            detailed_messages.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # STEP 4: Return paginated result
            result = {
                'messages': detailed_messages,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
                'date_range': {
                    'start': since_date.isoformat(),
                    'end': until_date.isoformat(),
                    'days_back': days_back
                },
                'bank_senders_used': user_bank_senders
            }
            
            logger.info(f"Found {len(detailed_messages)} messages from user's bank senders for integration {self.integration.id} (page {page}/{total_pages})")
            return result
            
        except HttpError as e:
            logger.error(f"Gmail API error getting banking messages for integration {self.integration.id}: {str(e)}")
            return {
                'messages': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'has_next': False,
                'has_previous': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error getting banking messages for integration {self.integration.id}: {str(e)}")
            return {
                'messages': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'has_next': False,
                'has_previous': False,
                'error': str(e)
            }
    
    def refresh_tokens_if_needed(self) -> bool:
        """Refresh OAuth tokens if needed"""
        try:
            oauth_tokens = self.get_oauth_tokens()
            if not oauth_tokens or 'refresh_token' not in oauth_tokens:
                return False
            
            # Create credentials and try to refresh
            credentials = Credentials(
                token=oauth_tokens.get('access_token'),
                refresh_token=oauth_tokens.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=oauth_tokens.get('client_id'),
                client_secret=oauth_tokens.get('client_secret')
            )
            
            # Check if token needs refresh
            if credentials.expired and credentials.refresh_token:
                credentials.refresh()
                
                # Save new tokens
                updated_tokens = {
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'expires_at': credentials.expiry.isoformat() if credentials.expiry else None
                }
                
                self.save_oauth_tokens(updated_tokens)
                logger.info(f"Refreshed OAuth tokens for integration {self.integration.id}")
                return True
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh tokens for integration {self.integration.id}: {str(e)}")
            return False
    
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
                'provider_message_id': message['id'],  # Gmail ID
                'thread_id': message['threadId'],
                'subject': subject,
                'sender': sender,
                'recipient': to,
                'date': date,
                'timestamp': timestamp,
                'body': body,
                'snippet': message.get('snippet', ''),
                'labels': message.get('labelIds', []),
                'raw_headers': {h['name']: h['value'] for h in headers},
                'attachment_count': self._count_attachments(message['payload'])
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
                        # Basic HTML stripping
                        body = re.sub(r'<[^>]+>', '', html_body)
        
        return body.strip()
    
    def _count_attachments(self, payload: Dict[str, Any]) -> int:
        """Count attachments in message"""
        attachment_count = 0
        
        if payload.get('parts'):
            for part in payload['parts']:
                if part.get('filename') and part.get('body', {}).get('attachmentId'):
                    attachment_count += 1
        
        return attachment_count
    
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