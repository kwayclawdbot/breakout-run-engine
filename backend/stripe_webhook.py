#!/usr/bin/env python3
"""
Stripe Webhook Handler for Breakout Alerts
Handles payment confirmations and user activation
"""

import os
import sys
import json
import hmac
import hashlib
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

class StripeWebhookHandler:
    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    def verify_signature(self, payload: bytes, sig_header: str) -> bool:
        """Verify Stripe webhook signature"""
        if not self.webhook_secret:
            return True  # Skip verification in development
        
        try:
            timestamp, signature = sig_header.split(',')
            timestamp = timestamp.split('=')[1]
            signature = signature.split('=')[1]
            
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_sig = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_sig, signature)
        except:
            return False
    
    def handle_checkout_completed(self, session: dict):
        """Handle successful checkout - activate user"""
        try:
            # Get customer email or phone from session
            customer_email = session.get('customer_details', {}).get('email', '')
            customer_phone = session.get('customer_details', {}).get('phone', '')
            
            # Find user by email or phone
            user = None
            if customer_email:
                result = self.supabase.table('users').select('*').eq('email', customer_email).execute()
                if result.data:
                    user = result.data[0]
            
            if not user and customer_phone:
                # Clean phone number
                phone = customer_phone.replace('+', '').replace('-', '').replace(' ', '')
                result = self.supabase.table('users').select('*').eq('phone', f"+{phone}").execute()
                if result.data:
                    user = result.data[0]
            
            if not user:
                print(f"⚠️ No user found for email: {customer_email}, phone: {customer_phone}")
                return {'status': 'error', 'message': 'User not found'}
            
            # Determine tier from line items
            tier = self._get_tier_from_session(session)
            
            # Update user status to active
            self.supabase.table('users').update({
                'status': 'active',
                'membership_tier': tier,
                'stripe_customer_id': session.get('customer', ''),
                'stripe_subscription_id': session.get('subscription', ''),
                'updated_at': datetime.now().isoformat()
            }).eq('id', user['id']).execute()
            
            print(f"✅ Activated user: {user.get('name', 'Unknown')} - Tier: {tier}")
            
            # Send welcome SMS
            self._send_welcome_sms(user, tier)
            
            return {'status': 'success', 'user_id': user['id'], 'tier': tier}
            
        except Exception as e:
            print(f"❌ Error handling checkout: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_tier_from_session(self, session: dict) -> str:
        """Determine tier from checkout session"""
        try:
            line_items = session.get('line_items', {}).get('data', [])
            if line_items:
                price_id = line_items[0].get('price', {}).get('id', '')
                # Map price IDs to tiers
                tier_map = {
                    'price_basic': 'basic',
                    'price_pro': 'pro',
                    'price_vip': 'vip',
                }
                for key, tier in tier_map.items():
                    if key in price_id.lower():
                        return tier
            
            # Fallback: check amount
            amount = session.get('amount_total', 0)
            if amount == 2900:  # $29
                return 'basic'
            elif amount == 4900:  # $49
                return 'pro'
            elif amount == 9900:  # $99
                return 'vip'
            
            return 'basic'  # Default
        except:
            return 'basic'
    
    def _send_welcome_sms(self, user: dict, tier: str):
        """Send welcome SMS after payment"""
        try:
            from twilio.rest import Client
            
            twilio = Client(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
            
            name = user.get('name', 'Trader')
            phone = user.get('phone')
            
            if not phone:
                return
            
            tier_limits = {
                'basic': '1',
                'pro': '3',
                'vip': '10'
            }
            
            message = f"""Welcome to Breakout Alerts, {name}! 🎉

You're now a {tier.upper()} member!
Daily alerts: {tier_limits.get(tier, '1')} per day

First scan: Tomorrow 8:30 AM ET

Questions? Reply here anytime.

Let's catch some breakouts! 📈"""
            
            twilio.messages.create(
                body=message,
                from_=os.getenv('TWILIO_PHONE_NUMBER'),
                to=phone
            )
            
            print(f"✅ Welcome SMS sent to {name}")
            
        except Exception as e:
            print(f"⚠️ Could not send welcome SMS: {e}")
    
    def handle_subscription_cancelled(self, subscription: dict):
        """Handle subscription cancellation"""
        try:
            customer_id = subscription.get('customer', '')
            
            # Find user by stripe customer ID
            result = self.supabase.table('users').select('*').eq('stripe_customer_id', customer_id).execute()
            
            if not result.data:
                print(f"⚠️ No user found for customer: {customer_id}")
                return {'status': 'error', 'message': 'User not found'}
            
            user = result.data[0]
            
            # Deactivate user
            self.supabase.table('users').update({
                'status': 'cancelled',
                'updated_at': datetime.now().isoformat()
            }).eq('id', user['id']).execute()
            
            print(f"✅ Deactivated user: {user.get('name', 'Unknown')}")
            return {'status': 'success', 'user_id': user['id']}
            
        except Exception as e:
            print(f"❌ Error handling cancellation: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def process_webhook(self, payload: bytes, sig_header: str) -> dict:
        """Main webhook processing"""
        # Verify signature
        if not self.verify_signature(payload, sig_header):
            return {'status': 'error', 'message': 'Invalid signature'}
        
        try:
            event = json.loads(payload)
            event_type = event.get('type', '')
            
            print(f"📩 Stripe webhook received: {event_type}")
            
            if event_type == 'checkout.session.completed':
                return self.handle_checkout_completed(event['data']['object'])
            
            elif event_type == 'customer.subscription.deleted':
                return self.handle_subscription_cancelled(event['data']['object'])
            
            elif event_type == 'invoice.paid':
                # Handle recurring payment
                print("✅ Recurring payment received")
                return {'status': 'success', 'message': 'Recurring payment noted'}
            
            else:
                return {'status': 'ignored', 'message': f'Event type: {event_type}'}
                
        except Exception as e:
            print(f"❌ Webhook processing error: {e}")
            return {'status': 'error', 'message': str(e)}


if __name__ == "__main__":
    # Test the webhook handler
    handler = StripeWebhookHandler()
    print("✅ Stripe webhook handler initialized")
