import MetaTrader5 as mt5
import time
from config.settings import Config
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import AdvancedLogger
from utils.telegram_notifier import TelegramNotifier



class TradeExecutor:
    def __init__(self, mt5_connector):
        self.mt5 = mt5_connector
        self.config = Config()
        self.open_positions = []
        self.logger = AdvancedLogger()
        self.notifier = TelegramNotifier()  # ✅ Telegram only
    
    def execute_trade(self, symbol, signal, lot_size=0.01):
        """Execute trade based on signal"""
        try:
            if not self.mt5.connected:
                print("❌ Not connected to MT5")
                return False
                
            # Check risk management first
            if not self._check_risk_management():
                print("❌ Risk management check failed")
                return False
                
            # Check max open positions
            if not self._check_max_positions():
                print("❌ Max positions reached")
                return False
                
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                print(f"❌ Cannot get tick data for {symbol}")
                return False
                
            # Get account info for logging
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Cannot get account info")
                return False
                
            # Prepare order request
            if signal == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            elif signal == "SELL":
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                print("❌ Invalid signal")
                return False
                
            # Calculate position size based on risk
            lot_size = self._calculate_position_size(symbol, price)
            if lot_size <= 0:
                print("❌ Invalid position size")
                return False
                
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "deviation": 10,
                "magic": 2024,
                "comment": f"AI Scalping {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"❌ Order failed: {result.retcode}")
                return False
                
            print(f"✅ Trade executed: {signal} {symbol} {lot_size} lots")
            print(f"   Price: {price}, Ticket: {result.order}")
            
            # ✅ TELEGRAM NOTIFICATION - Trade executed
            self.notifier.send_trade_notification(
                symbol=symbol,
                action=signal,
                price=price,
                volume=lot_size,
                ticket=result.order
            )
            
            # Track open position
            self.open_positions.append({
                'ticket': result.order,
                'symbol': symbol,
                'type': signal,
                'volume': lot_size,
                'open_price': price,
                'open_time': time.time()
            })
            
            # Log the trade
            trade_log_data = {
                'symbol': symbol,
                'signal': signal,
                'action': 'OPEN',
                'volume': lot_size,
                'entry_price': price,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'ticket': result.order,
                'status': 'OPEN'
            }
            self.logger.log_trade(trade_log_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Trade execution error: {e}")
            return False 
    
    def _calculate_position_size(self, symbol, price):
        """Calculate position size based on risk management"""
        risk_settings = self.config.get_risk_settings()
        account_info = mt5.account_info()
        
        if account_info is None:
            return 0.01  # default fallback
            
        # Risk per trade (0.75% of balance)
        risk_amount = account_info.balance * (risk_settings['max_daily_loss_percent'] / 100) / 3
        stop_loss_pips = 6  # Fixed SL for scalping
        
        # Calculate lot size (simplified)
        pip_value = 10  # For EURUSD
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Ensure minimum and maximum lot size
        lot_size = max(0.01, min(lot_size, 1.0))  # Min 0.01, Max 1.0
        return round(lot_size, 2)
    
    def _check_risk_management(self):
        """Check daily loss limit and drawdown"""
        risk_settings = self.config.get_risk_settings()
        account_info = mt5.account_info()
        
        if account_info is None:
            return False
            
        # Calculate daily PnL (simplified)
        daily_pnl = account_info.equity - account_info.balance
        
        # Check daily loss limit
        max_daily_loss = account_info.balance * (risk_settings['max_daily_loss_percent'] / 100)
        if daily_pnl <= -max_daily_loss:
            print(f"❌ Daily loss limit reached: {daily_pnl:.2f}")
            return False
            
        # Check account drawdown
        drawdown = (account_info.balance - account_info.equity) / account_info.balance * 100
        if drawdown >= risk_settings['max_account_drawdown']:
            print(f"❌ Max drawdown reached: {drawdown:.2f}%")
            return False
            
        return True
    
    def _check_max_positions(self):
        """Check maximum open positions"""
        market_settings = self.config.get_market_settings()
        positions = mt5.positions_get()
        
        if positions is None:
            return True  # No positions open
            
        current_positions = len(positions)
        max_positions = market_settings['max_open_positions']
        
        if current_positions >= max_positions:
            print(f"❌ Max positions reached: {current_positions}/{max_positions}")
            return False
            
        return True
    
    def close_all_positions(self):
        """Close all open positions"""
        try:
            positions = mt5.positions_get()
            if positions:
                for position in positions:
                    self.close_position(position.ticket)
            print("✅ All positions closed")
        except Exception as e:
            print(f"❌ Error closing positions: {e}")
    
    def close_position(self, ticket):
        """Close specific position"""
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
                
            position = position[0]
            tick = mt5.symbol_info_tick(position.symbol)
            
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": position.ticket,
                "price": price,
                "deviation": 10,
                "magic": 2024,
                "comment": "AI Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Position closed: {position.symbol}")
                
                # ✅ LOG THE CLOSE TRADE
                account_info = mt5.account_info()
                if account_info:
                    profit = position.profit
                    trade_log_data = {
                        'symbol': position.symbol,
                        'signal': 'CLOSE',
                        'action': 'CLOSE',
                        'volume': position.volume,
                        'entry_price': position.price_open,
                        'exit_price': price,
                        'profit': profit,
                        'balance': account_info.balance,
                        'equity': account_info.equity,
                        'ticket': ticket,
                        'status': 'CLOSED'
                    }
                    self.logger.log_trade(trade_log_data)
                
                return True
            else:
                print(f"❌ Close position failed: {result.retcode}")
                return False
                
        except Exception as e:
            print(f"❌ Error closing position: {e}")
            return False

# Test function
def test_executor():
    from core.mt5_connector import MT5Connector
    
    print("Testing Trade Executor...")
    connector = MT5Connector()
    
    if connector.connect():
        executor = TradeExecutor(connector)
        
        # Test risk management
        print("🔍 Testing risk management...")
        risk_ok = executor._check_risk_management()
        print(f"Risk Management: {'✅ PASS' if risk_ok else '❌ FAIL'}")
        
        # Test position sizing
        lot_size = executor._calculate_position_size("EURUSD", 1.0850)
        print(f"Calculated Lot Size: {lot_size}")
        
        connector.disconnect()

if __name__ == "__main__":
    test_executor()