from utils.telegram_notifier import TelegramNotifier

def test_startup():
    print("Testing startup notification...")
    
    notifier = TelegramNotifier()
    
    # Test startup notification
    success = notifier.send_startup_notification(
        account_info={
            'server': 'OctaFX-Demo',
            'login': '213700671', 
            'balance': 5000.0,
            'equity': 5000.0
        },
        pairs=['EURUSD', 'GBPUSD', 'XAUUSD', 'USDJPY', 'AUDUSD']
    )
    
    if success:
        print("✅ Startup notification sent!")
    else:
        print("❌ Failed to send startup notification")

if __name__ == "__main__":
    test_startup()