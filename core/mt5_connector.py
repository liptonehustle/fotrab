import sys
import os
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
import MetaTrader5 as mt5
import time

class MT5Connector:
    def __init__(self):
        self.config = Config()
        self.connected = False
        
    def connect(self):
        """Connect to MT5 terminal"""
        try:
            broker_config = self.config.get_broker_settings()
            
            print(f"🔧 Attempting to connect to: {broker_config['server']}")
            print(f"🔧 Login: {broker_config['login']}")
            
            # Initialize MT5
            if not mt5.initialize():
                error_code = mt5.last_error()
                print(f"❌ MT5 initialization failed. Error code: {error_code}")
                return False
                    
            print("✅ MT5 initialized successfully")
                    
            # Login to account - returns True/False
            login_success = mt5.login(
                login=broker_config['login'],
                password=broker_config['password'],
                server=broker_config['server']
            )
            
            if not login_success:
                error_code = mt5.last_error()
                print(f"❌ Login failed. Error code: {error_code}")
                return False
                
            # Get account info separately
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Could not get account info")
                return False
                    
            self.connected = True
            print(f"✅ Connected to MT5 successfully!")
            print(f"   Account: {account_info.login}")
            print(f"   Balance: {account_info.balance}")
            print(f"   Equity: {account_info.equity}")
            return True
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("✅ Disconnected from MT5")
    
    def get_account_info(self):
        """Get current account information"""
        if not self.connected:
            print("❌ Not connected to MT5")
            return None
            
        account_info = mt5.account_info()
        if account_info:
            return {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'leverage': account_info.leverage
            }
        return None
    
    def test_connection(self):
        """Test the MT5 connection"""
        print("Testing MT5 connection...")
        if self.connect():
            account_info = self.get_account_info()
            if account_info:
                print(f"💰 Account Balance: {account_info['balance']}")
                print(f"📈 Equity: {account_info['equity']}")
                print(f"🎯 Free Margin: {account_info['free_margin']}")
            self.disconnect()
            return True
        return False

# Test function
if __name__ == "__main__":
    connector = MT5Connector()
    connector.test_connection()