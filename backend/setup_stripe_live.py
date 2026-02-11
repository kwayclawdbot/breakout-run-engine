#!/usr/bin/env python3
"""
Create Stripe LIVE Payment Links for Breakout Alerts Production
Run this AFTER you have your live Stripe account set up
"""

import stripe
import os
from dotenv import load_dotenv

# Instructions for going live
print("""
╔══════════════════════════════════════════════════════════════════╗
║  STRIPE LIVE MODE SETUP - BREAKOUT ALERTS                        ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1: Get Live API Key
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to: https://dashboard.stripe.com/apikeys
2. Toggle "View test data" OFF (top right)
3. Copy your Secret key (starts with sk_live_...)
4. Update .env file:
   STRIPE_SECRET_KEY=sk_live_...

STEP 2: Create Products & Prices
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to: https://dashboard.stripe.com/products
2. Click "+ Add product"
3. Create 3 products:

   Product: Breakout Alerts - Basic
   ├─ Price: $29/month
   └─ Recurring: Monthly
   
   Product: Breakout Alerts - Pro  
   ├─ Price: $49/month
   └─ Recurring: Monthly
   
   Product: Breakout Alerts - VIP
   ├─ Price: $99/month
   └─ Recurring: Monthly

4. Copy the Price IDs (start with price_...)

STEP 3: Create Payment Links
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. For each product, click "Create payment link"
2. Settings:
   - Collect: Email + Phone number (required)
   - After payment: Redirect to your success page
   - Redirect URL: https://web-ui-lac.vercel.app/success?session_id={CHECKOUT_SESSION_ID}
3. Copy the Payment Link URLs

STEP 4: Configure Webhook
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to: https://dashboard.stripe.com/webhooks
2. Click "+ Add endpoint"
3. Endpoint URL: https://breakout-run-api.onrender.com/webhook/stripe
4. Select events:
   ☑ checkout.session.completed
   ☑ customer.subscription.deleted
   ☑ invoice.paid
5. Click "Add endpoint"
6. Copy the "Signing secret" (starts with whsec_...)
7. Update .env file:
   STRIPE_WEBHOOK_SECRET=whsec_...

STEP 5: Update Code
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Replace these in sms_onboarding_fixed.py:

self.stripe_links = {
    'basic': 'https://buy.stripe.com/YOUR_LIVE_BASIC_LINK',
    'pro': 'https://buy.stripe.com/YOUR_LIVE_PRO_LINK',
    'vip': 'https://buy.stripe.com/YOUR_LIVE_VIP_LINK'
}

STEP 6: Test Live Mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Use a real card (small amount will be charged)
2. Complete payment
3. Check webhook logs in Stripe dashboard
4. Verify user activated in Supabase
5. Check for welcome SMS

STEP 7: Go Live
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Deploy backend to Render with live keys
2. Test complete flow end-to-end
3. Monitor first few signups closely
4. Set up Stripe email notifications for failed payments

""")

# Load current keys
load_dotenv()
current_key = os.getenv('STRIPE_SECRET_KEY', '')

if 'sk_live' in current_key:
    print("✅ You already have a LIVE key configured!")
    print(f"   Key: {current_key[:20]}...")
    
    stripe.api_key = current_key
    
    try:
        print("\n📊 Your Live Products:")
        for product in stripe.Product.list(limit=10):
            if 'breakout' in product.name.lower():
                print(f"  • {product.name}: {product.id}")
        
        print("\n💳 Your Live Prices:")
        for price in stripe.Price.list(limit=10):
            if hasattr(price, 'product') and price.product:
                try:
                    prod = stripe.Product.retrieve(price.product)
                    if 'breakout' in prod.name.lower():
                        amount = price.unit_amount / 100
                        print(f"  • {prod.name}: ${amount}/mo - {price.id}")
                except:
                    pass
        
        print("\n🔗 Your Payment Links:")
        for link in stripe.PaymentLink.list(limit=10):
            print(f"  • {link.url}")
            
    except Exception as e:
        print(f"❌ Error fetching live data: {e}")
else:
    print("⚠️  You currently have TEST mode configured")
    print(f"   Current key: {current_key[:20]}...")
    print("\n👆 Follow STEP 1 above to switch to LIVE mode")
