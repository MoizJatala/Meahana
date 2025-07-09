#!/usr/bin/env python3
"""
Configuration script for external ngrok tunnel
"""

import requests
import json
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


def test_service_health():
    """Test if the service is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Service is not accessible: {e}")
        return False


def set_external_ngrok_url(external_url: str):
    """Set external ngrok URL"""
    try:
        response = requests.post(
            f"{BASE_URL}/ngrok/set-external-url",
            json={"external_url": external_url}
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ External ngrok URL set successfully!")
            logger.info(f"🌐 Public URL: {data['data']['external_url']}")
            logger.info(f"🔗 Webhook URL: {data['data']['webhook_url']}")
            return True
        else:
            logger.error(f"❌ Failed to set external URL: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error setting external URL: {e}")
        return False


def check_ngrok_status():
    """Check current ngrok status"""
    try:
        response = requests.get(f"{BASE_URL}/ngrok/status")
        
        if response.status_code == 200:
            data = response.json()
            info = data.get("data", {})
            
            logger.info("📋 Current ngrok status:")
            logger.info(f"🔸 Status: {'Running' if info.get('is_running') else 'Not Running'}")
            logger.info(f"🔸 Public URL: {info.get('public_url', 'N/A')}")
            logger.info(f"🔸 Webhook URL: {info.get('webhook_url', 'N/A')}")
            logger.info(f"🔸 External URL: {info.get('external_url', 'N/A')}")
            logger.info(f"🔸 Managed Externally: {info.get('managed_externally', False)}")
            
            return info
        else:
            logger.error(f"❌ Failed to get status: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error getting status: {e}")
        return None


def refresh_detection():
    """Refresh external tunnel detection"""
    try:
        response = requests.post(f"{BASE_URL}/ngrok/refresh-detection")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ External tunnel detection refreshed")
            return data.get("data", {})
        else:
            logger.error(f"❌ Failed to refresh detection: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error refreshing detection: {e}")
        return None


def test_webhook(webhook_url: str):
    """Test webhook endpoint"""
    test_payload = {
        "event": "test.configuration",
        "data": {
            "bot_id": "config_test_bot",
            "test": True
        }
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Webhook test successful!")
            return True
        else:
            logger.error(f"❌ Webhook test failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Webhook test error: {e}")
        return False


def test_bot_creation():
    """Test bot creation endpoint"""
    test_data = {
        "meeting_url": "https://meet.google.com/config-test-meeting",
        "bot_name": "Configuration Test Bot"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/bots/",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Bot creation test successful!")
            logger.info(f"🤖 Meeting ID: {data.get('id')}")
            logger.info(f"📝 Status: {data.get('status')}")
            logger.info(f"🔗 Meeting URL: {data.get('meeting_url')}")
            return True
        else:
            logger.error(f"❌ Bot creation test failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Bot creation test error: {e}")
        return False


def main():
    """Main configuration function"""
    print("🚀 ngrok External Tunnel Configuration")
    print("=" * 50)
    
    # Test service health
    if not test_service_health():
        print("❌ Service is not running. Please start the service first:")
        print("   docker-compose up --build")
        return
    
    print("✅ Service is running!")
    print()
    
    # Check current status
    print("🔍 Checking current ngrok status...")
    status = check_ngrok_status()
    print()
    
    # Set your external ngrok URL
    external_url = "https://7d116bbcc6be.ngrok-free.app"
    
    print(f"🔧 Setting external ngrok URL to: {external_url}")
    if set_external_ngrok_url(external_url):
        print()
        
        # Refresh detection
        print("🔄 Refreshing external tunnel detection...")
        refresh_detection()
        print()
        
        # Check final status
        print("📊 Final ngrok status:")
        final_status = check_ngrok_status()
        
        if final_status and final_status.get("webhook_url"):
            print()
            print("🧪 Testing webhook endpoint...")
            webhook_url = final_status["webhook_url"]
            webhook_success = test_webhook(webhook_url)
            
            print()
            print("🤖 Testing bot creation...")
            bot_success = test_bot_creation()
            
            if webhook_success and bot_success:
                print()
                print("🎉 Configuration complete! Your external ngrok tunnel is ready!")
                print(f"🔗 Webhook URL: {webhook_url}")
                print()
                print("✅ Your system is now configured to:")
                print("   • Use your external ngrok tunnel automatically")
                print("   • Receive real-time webhook events during meetings")
                print("   • Store all webhook events in the database")
                print("   • Process transcripts and generate AI analysis")
                print()
                print("🚀 Ready for real meetings! Next steps:")
                print("1. Create a meeting:")
                print(f'   curl -X POST {BASE_URL}/api/v1/bots/ \\')
                print('     -H "Content-Type: application/json" \\')
                print('     -d \'{"meeting_url": "https://meet.google.com/your-meeting", "bot_name": "My Bot"}\'')
                print()
                print("2. Join your meeting and watch the webhook events in real-time!")
                print("3. Check logs: docker-compose logs web --follow")
            else:
                print("⚠️ Some tests failed. Please check the logs above.")
        else:
            print("❌ Configuration failed. Please check the logs above.")
    else:
        print("❌ Failed to set external URL. Please check your setup.")


if __name__ == "__main__":
    main() 