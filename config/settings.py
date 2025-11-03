import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
    def get_broker_settings(self):
        return {
            'server': os.getenv('MT5_SERVER', 'OctaFX-Demo'),
            'login': int(os.getenv('MT5_LOGIN', '0')),
            'password': os.getenv('MT5_PASSWORD', ''),
            'demo_mode': os.getenv('MT5_DEMO_MODE', 'true').lower() == 'true'
        }
    
    def get_market_settings(self):
        pairs = os.getenv('DEFAULT_PAIRS', 'EURUSD,GBPUSD,USDJPY')
        return {
            'default_pairs': pairs.split(','),
            'auto_top_gainers': os.getenv('AUTO_TOP_GAINERS', 'false').lower() == 'true',
            'max_open_positions': int(os.getenv('MAX_OPEN_POSITIONS', '3'))
        }
    
    def get_risk_settings(self):
        return {
            'max_daily_loss_percent': float(os.getenv('MAX_DAILY_LOSS_PERCENT', '3.0')),
            'max_account_drawdown': float(os.getenv('MAX_ACCOUNT_DRAWDOWN', '10.0'))
        }

# Test function
def test_config():
    config = Config()
    print("Broker Settings:", config.get_broker_settings())
    print("Market Settings:", config.get_market_settings())
    print("Risk Settings:", config.get_risk_settings())

if __name__ == "__main__":
    test_config()