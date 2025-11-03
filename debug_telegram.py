import requests
import os
from dotenv import load_dotenv

load_dotenv()

def debug_telegram():
    print("🔧 Debugging Telegram Configuration...")
    
    # Check environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    enabled = os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
    
    print(f"TELEGRAM_ENABLED: {enabled}")
    print(f"TELEGRAM_BOT_TOKEN: {bot_token[:10]}...{bot_token[-10:] if bot_token else 'NOT FOUND'}")
    print(f"TELEGRAM_CHAT_ID: {chat_id}")
    
    if not bot_token or not chat_id:
        print("❌ Missing Telegram credentials in .env file")
        return
    
    # Test API connection
    print("\n🔍 Testing Telegram API...")
    
    # Method 1: Get bot info
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    try:
        response = requests.get(url, timeout=10)
        print(f"Bot Info Status: {response.status_code}")
        if response.status_code == 200:
            bot_data = response.json()
            print(f"✅ Bot found: {bot_data['result']['first_name']} (@{bot_data['result']['username']})")
        else:
            print(f"❌ Bot not found: {response.text}")
            return
    except Exception as e:
        print(f"❌ API Error: {e}")
        return
    
    # Method 2: Test send message
    print("\n🔍 Testing message send...")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': '🔧 Test message from AI Trading System',
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Send Message Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Message sent successfully!")
            print("📱 Check your Telegram for the test message")
        elif response.status_code == 400:
            error_data = response.json()
            print(f"❌ Bad Request: {error_data.get('description', 'Unknown error')}")
            if "chat not found" in error_data.get('description', '').lower():
                print("💡 Solution: Send a message to your bot first, then get new chat_id")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Send Error: {e}")

if __name__ == "__main__":
    debug_telegram()