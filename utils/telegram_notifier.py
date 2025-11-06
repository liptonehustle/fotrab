import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

class TelegramNotifier:
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
        
        print(f"🔧 Telegram Config - Enabled: {self.enabled}, Token: {bool(self.bot_token)}, Chat ID: {bool(self.chat_id)}")
        
        if self.enabled and self.bot_token and self.chat_id:
            print("✅ Telegram notifier initialized successfully!")
        elif self.enabled:
            print("❌ Telegram credentials missing")
    
    def send_message(self, message):
        """Send message to Telegram"""
        if not self.enabled:
            print("❌ Telegram notifications disabled")
            return False
            
        if not self.bot_token or not self.chat_id:
            print("❌ Telegram credentials missing - check .env file")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("✅ Telegram message sent successfully!")
                return True
            else:
                print(f"❌ Telegram send failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def send_startup_notification(self, account_info, pairs):
        """Send startup notification when live trading begins"""
        message = f"""
🚀 <b>AI TRADING SYSTEM STARTED</b> 🚀

<b>Account Info:</b>
• Broker: {account_info.get('server', 'N/A')}
• Account: {account_info.get('login', 'N/A')}
• Balance: ${account_info.get('balance', 0):.2f}
• Equity: ${account_info.get('equity', 0):.2f}

<b>Trading Pairs:</b>
{chr(10).join(f'• {pair}' for pair in pairs)}

<b>Risk Management:</b>
• Max Positions: {os.getenv('MAX_OPEN_POSITIONS', 3)}
• Daily Loss Limit: {os.getenv('MAX_DAILY_LOSS_PERCENT', 3.0)}%
• Max Drawdown: {os.getenv('MAX_ACCOUNT_DRAWDOWN', 10.0)}%

<b>Start Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 <i>System is now live and monitoring markets!</i>
"""
        success = self.send_message(message)
        if success:
            print("✅ Startup notification sent!")
        return success
    
    def send_shutdown_notification(self, duration_minutes, performance_data):
        """Send shutdown notification when trading stops"""
        message = f"""
🛑 <b>AI TRADING SYSTEM STOPPED</b> 🛑

<b>Session Summary:</b>
• Duration: {duration_minutes:.1f} minutes
• Total Trades: {performance_data.get('total_trades', 0)}
• Win Rate: {performance_data.get('win_rate', 0):.1f}%
• Total Profit: ${performance_data.get('total_profit', 0):.2f}

<b>Stop Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 <i>Check logs for detailed performance analysis</i>
"""
        success = self.send_message(message)
        if success:
            print("✅ Shutdown notification sent!")
        return success
    
    def send_error_notification(self, error_message):
        """Send error notification"""
        message = f"""
🚨 <b>SYSTEM ERROR</b> 🚨

<b>Error:</b> {error_message}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ <i>Please check the trading system!</i>
"""
        success = self.send_message(message)
        if success:
            print("✅ Error notification sent!")
        return success
    
    def send_trade_notification(self, symbol, action, price, volume, ticket=None, stop_loss=None, take_profit=None):
        """Send trade execution notification with TP/SL"""
        emoji = "🟢" if action == "BUY" else "🔴"
        
        # Format TP/SL info
        tp_sl_info = ""
        if stop_loss and take_profit:
            sl_pips = abs(price - stop_loss) * 10000
            tp_pips = abs(price - take_profit) * 10000
            tp_sl_info = f"\n<b>Stop Loss:</b> {stop_loss:.5f} ({sl_pips:.1f}pips)"
            tp_sl_info += f"\n<b>Take Profit:</b> {take_profit:.5f} ({tp_pips:.1f}pips)"
        
        message = f"""
    {emoji} <b>TRADE EXECUTED</b> {emoji}

    <b>Pair:</b> {symbol}
    <b>Action:</b> {action}
    <b>Price:</b> {price:.5f}
    <b>Volume:</b> {volume:.2f} lots
    <b>Ticket:</b> {ticket if ticket else 'N/A'}{tp_sl_info}

    <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    🤖 <i>AI Trading System</i>
    """
        success = self.send_message(message)
        if success:
            print(f"✅ Telegram trade notification sent: {action} {symbol}")
        return success
    
    def send_signal_notification(self, symbol, signal, price, indicators):
        """Send trading signal notification"""
        if signal == "NO_SIGNAL":
            return False
            
        emoji = "🟢" if signal == "BUY" else "🔴"
        
        message = f"""
🎯 <b>TRADING SIGNAL</b> 🎯

<b>Pair:</b> {symbol}
<b>Signal:</b> {signal} {emoji}
<b>Current Price:</b> {price:.5f}

<b>Technical Indicators:</b>
• RSI: {indicators.get('rsi', 0):.1f}
• SMA10/SMA20: {indicators.get('sma_10', 0):.5f}/{indicators.get('sma_20', 0):.5f}
• Stochastic K: {indicators.get('stoch_k', 0):.1f}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 <i>AI Trading System - Monitoring</i>
"""
        success = self.send_message(message)
        if success:
            print(f"✅ Telegram signal notification sent: {signal} {symbol}")
        else:
            print(f"❌ Failed to send Telegram signal notification")
        return success

# Test function
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
        print("✅ Startup notification test passed!")
    else:
        print("❌ Startup notification test failed")

if __name__ == "__main__":
    test_startup()