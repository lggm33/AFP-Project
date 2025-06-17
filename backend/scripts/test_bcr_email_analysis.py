#!/usr/bin/env python3
"""
BCR Email Analysis Test Script with Multi-Strategy Approach
Tests different extraction strategies for SINPE and Credit Card emails
Based on run_bcr_test.py structure for better error handling
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

import json
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from openai import OpenAI
from core.gmail_service import GmailService
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount

class EmailAnalysisStrategies:
    """Handles different extraction strategies for email analysis"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        
    def analyze_email_structure(self, html_content, email_type="unknown"):
        """
        LLM analyzes email structure and suggests multiple extraction strategies
        """
        prompt = f"""
        Analyze this HTML email structure and suggest the BEST extraction strategies for financial transaction data.
        
        Email Type: {email_type}
        
        I need to extract these UNIVERSAL fields (always required):
        - timestamp (fecha/date)
        - amount (monto)
        - transaction_type (can be inferred from email context)
        - source_bank (can be inferred as "BCR")
        
        Optional fields (if available):
        - currency (moneda)
        - merchant/recipient (comercio/destinatario)
        - reference_id (referencia)
        - status (estado)
        
        For each field, suggest up to 3 different extraction strategies ranked by confidence:
        1. CSS_SELECTOR: If data is in structured HTML elements
        2. REGEX: If data is in plain text within HTML
        3. XPATH: If complex navigation is needed
        
        Return JSON format:
        {{
            "email_structure_analysis": "description of HTML structure",
            "recommended_approach": "primary strategy type",
            "field_strategies": {{
                "timestamp": [
                    {{"strategy": "regex", "confidence": 0.9, "instruction": "regex pattern or selector"}},
                    {{"strategy": "css_selector", "confidence": 0.7, "instruction": "css selector"}}
                ],
                "amount": [...],
                "transaction_type": [...],
                "currency": [...],
                "merchant_recipient": [...],
                "reference_id": [...],
                "status": [...]
            }}
        }}
        
        HTML Content:
        {html_content[:8000]}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in HTML parsing and data extraction for financial emails. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '{' in content and '}' in content:
                # Find the JSON object
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
            else:
                json_str = content
                
            return json.loads(json_str)
            
        except Exception as e:
            print(f"❌ Error analyzing email structure: {e}")
            return None
    
    def execute_css_strategy(self, html_content, instruction):
        """Execute CSS selector strategy"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            elements = soup.select(instruction)
            return [elem.get_text(strip=True) for elem in elements] if elements else []
        except Exception as e:
            return f"CSS Error: {e}"
    
    def execute_regex_strategy(self, html_content, instruction):
        """Execute regex strategy"""
        try:
            # Remove HTML tags for text-based regex
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()
            
            matches = re.findall(instruction, text_content, re.IGNORECASE | re.MULTILINE)
            return matches if matches else []
        except Exception as e:
            return f"Regex Error: {e}"
    
    def execute_xpath_strategy(self, html_content, instruction):
        """Execute XPath strategy (simplified)"""
        # For now, convert simple XPath to CSS selector
        try:
            if instruction.startswith('//'):
                # Convert basic XPath to CSS
                css_equivalent = instruction.replace('//', '').replace('/', ' > ')
                return self.execute_css_strategy(html_content, css_equivalent)
            else:
                return f"XPath not fully implemented: {instruction}"
        except Exception as e:
            return f"XPath Error: {e}"
    
    def execute_strategy(self, html_content, strategy_type, instruction):
        """Execute a specific extraction strategy"""
        if strategy_type.lower() == 'css_selector':
            return self.execute_css_strategy(html_content, instruction)
        elif strategy_type.lower() == 'regex':
            return self.execute_regex_strategy(html_content, instruction)
        elif strategy_type.lower() == 'xpath':
            return self.execute_xpath_strategy(html_content, instruction)
        else:
            return f"Unknown strategy: {strategy_type}"

def get_user_email():
    """Get user email from user input"""
    print("👤 Please provide the email of a user with Gmail OAuth configured:")
    print("   (This should be a user in your Django database with Gmail access)")
    
    user_email = input("User email: ").strip()
    
    if not user_email:
        print("❌ No email provided")
        return None
    
    if '@' not in user_email:
        print("❌ Invalid email format")
        return None
    
    return user_email

def check_openai_key():
    """Check if OpenAI API key is set"""
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please run: export OPENAI_API_KEY='your-key-here'")
        return False
    
    print(f"✅ OpenAI API key found")
    return True

def get_html_from_message(message):
    """Extract HTML content from message"""
    # This is a simplified version - you might need to adapt based on your message structure
    html_content = ""
    
    # Try to get HTML content from the message body
    body = message.get('body', '')
    
    # If body contains HTML tags, use it as is
    if '<html>' in body.lower() or '<table>' in body.lower() or '<div>' in body.lower():
        html_content = body
    else:
        # Wrap plain text in basic HTML
        html_content = f"<html><body><p>{body}</p></body></html>"
    
    return html_content

def analyze_bcr_emails(user_email):
    """Analyze BCR emails with multi-strategy approach"""
    
    print("🚀 Starting Multi-Strategy BCR Email Analysis...")
    print("=" * 60)
    
    # Initialize services
    try:
        # Find user
        user = User.objects.filter(email=user_email).first()
        if not user:
            print(f"❌ No user found with email: {user_email}")
            return
            
        # Check if user has Google account
        google_account = SocialAccount.objects.filter(user=user, provider='google').first()
        if not google_account:
            print(f"❌ User {user_email} doesn't have Google OAuth configured")
            return
            
        print(f"📧 Using user: {user.username} ({user.email})")
        
        gmail_service = GmailService(user)
        print("✅ Gmail service initialized")
        
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        print("✅ OpenAI client initialized")
        
        strategies = EmailAnalysisStrategies(openai_client)
        print("✅ Analysis strategies initialized")
        
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        return
    
    # Specific BCR email senders we want to analyze
    email_configs = [
        {
            'sender': 'mensajero@bancobcr.com',
            'type': 'SINPE_MOVIL',
            'description': 'SINPE Mobile Transfer'
        },
        {
            'sender': 'bcrtarjestcta@bancobcr.com',
            'type': 'TARJETA_CREDITO',
            'description': 'Credit Card Transaction'
        }
    ]
    
    # Get ALL emails and filter manually
    print("\n📧 Fetching all recent emails...")
    all_messages = gmail_service.get_all_emails(max_results=200, days_back=90)
    
    if not all_messages:
        print("❌ No emails found")
        return
        
    print(f"✅ Found {len(all_messages)} total emails in the last 90 days")
    
    # Filter emails by specific BCR senders
    bcr_messages = []
    bcr_senders = ['mensajero@bancobcr.com', 'bcrtarjestcta@bancobcr.com']
    
    for message in all_messages:
        sender = message.get('sender', '').lower()
        for bcr_sender in bcr_senders:
            if bcr_sender.lower() in sender:
                bcr_messages.append(message)
                break
    
    print(f"🏦 Filtered to {len(bcr_messages)} emails from BCR senders:")
    for sender in bcr_senders:
        count = sum(1 for msg in bcr_messages if sender.lower() in msg.get('sender', '').lower())
        print(f"   📧 {sender}: {count} emails")
    
    for config in email_configs:
        print(f"\n🔍 ANALYZING {config['description'].upper()} EMAILS")
        print("-" * 50)
        
        # Filter messages for this specific sender
        matching_messages = []
        for message in bcr_messages:
            sender = message.get('sender', '').lower()
            if config['sender'].lower() in sender:
                matching_messages.append(message)
        
        if not matching_messages:
            print(f"❌ No emails found from {config['sender']}")
            continue
            
        print(f"📧 Found {len(matching_messages)} emails from {config['sender']}")
        
        # Show first few email subjects for verification
        print("📋 Email subjects found:")
        for i, msg in enumerate(matching_messages[:3]):
            print(f"   {i+1}. {msg.get('subject', 'No subject')[:80]}...")
        
        # Analyze first matching email
        message = matching_messages[0]
        html_content = get_html_from_message(message)
        
        print(f"📄 Email subject: {message.get('subject', 'No subject')}")
        print(f"📅 Email date: {message.get('date', 'No date')}")
        print(f"👤 From: {message.get('sender', 'Unknown sender')}")
        
        # 1. LLM analyzes structure and suggests strategies
        print("\n🧠 LLM analyzing email structure...")
        analysis = strategies.analyze_email_structure(html_content, config['type'])
        
        if not analysis:
            print("❌ Failed to analyze email structure")
            continue
            
        print(f"📊 Structure Analysis: {analysis.get('email_structure_analysis', 'No analysis')}")
        print(f"🎯 Recommended Approach: {analysis.get('recommended_approach', 'No recommendation')}")
        
        # 2. Execute all strategies for each field
        print(f"\n🔧 EXECUTING EXTRACTION STRATEGIES")
        print("-" * 40)
        
        field_results = {}
        
        for field_name, strategies_list in analysis.get('field_strategies', {}).items():
            print(f"\n🔍 Extracting: {field_name}")
            field_results[field_name] = []
            
            for strategy in strategies_list:
                strategy_type = strategy.get('strategy')
                instruction = strategy.get('instruction')
                confidence = strategy.get('confidence', 0.0)
                
                print(f"  🧪 Testing {strategy_type} (confidence: {confidence:.1f}): {instruction}")
                
                result = strategies.execute_strategy(html_content, strategy_type, instruction)
                
                # Determine if the strategy was successful
                is_success = False
                if result:
                    if isinstance(result, list) and result:
                        is_success = True
                    elif isinstance(result, str) and not result.startswith(('Error', 'CSS Error', 'Regex Error')):
                        is_success = True
                
                field_results[field_name].append({
                    'strategy': strategy_type,
                    'instruction': instruction,
                    'confidence': confidence,
                    'result': result,
                    'success': is_success
                })
                
                if isinstance(result, list) and result:
                    print(f"    ✅ Result: {result}")
                elif isinstance(result, str) and not result.startswith(('Error', 'CSS Error', 'Regex Error')):
                    print(f"    ✅ Result: {result}")
                else:
                    print(f"    ❌ Failed: {result}")
        
        # 3. Show summary and best strategies
        print(f"\n📋 EXTRACTION SUMMARY FOR {config['type']}")
        print("=" * 50)
        
        successful_extractions = 0
        total_fields = len(field_results)
        
        for field_name, results in field_results.items():
            successful_strategies = [r for r in results if r['success']]
            
            if successful_strategies:
                best_strategy = max(successful_strategies, key=lambda x: x['confidence'])
                print(f"✅ {field_name}: {best_strategy['result']} (via {best_strategy['strategy']})")
                successful_extractions += 1
            else:
                print(f"❌ {field_name}: No successful extraction")
        
        success_rate = (successful_extractions / total_fields) * 100 if total_fields > 0 else 0
        print(f"\n🎯 Success Rate: {successful_extractions}/{total_fields} ({success_rate:.1f}%)")
        
        # 4. Show recommended template configuration
        print(f"\n⚙️  RECOMMENDED TEMPLATE CONFIGURATION:")
        print("-" * 40)
        
        template_config = {
            'email_source': config['sender'],
            'transaction_type': config['type'],
            'extraction_strategies': {}
        }
        
        for field_name, results in field_results.items():
            successful_strategies = [r for r in results if r['success']]
            if successful_strategies:
                best_strategy = max(successful_strategies, key=lambda x: x['confidence'])
                template_config['extraction_strategies'][field_name] = {
                    'strategy': best_strategy['strategy'],
                    'instruction': best_strategy['instruction'],
                    'confidence': best_strategy['confidence']
                }
        
        print(json.dumps(template_config, indent=2, ensure_ascii=False))
    
    print(f"\n🎉 Multi-strategy analysis completed!")

def main():
    """Main execution function"""
    print("🧪 BCR EMAIL MULTI-STRATEGY ANALYSIS TEST")
    print("=" * 50)
    
    # Check OpenAI key
    if not check_openai_key():
        return
    
    # Get user email
    user_email = get_user_email()
    if not user_email:
        return
    
    print(f"\n🚀 Starting analysis for user: {user_email}")
    print("=" * 60)
    
    try:
        analyze_bcr_emails(user_email)
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()