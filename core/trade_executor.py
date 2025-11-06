import MetaTrader5 as mt5
import time
from config.settings import Config
from utils.logger import AdvancedLogger
from utils.telegram_notifier import TelegramNotifier

class TradeExecutor:
    def __init__(self, mt5_connector):
        self.mt5 = mt5_connector
        self.config = Config()
        self.open_positions = []
        self.logger = AdvancedLogger()
        self.notifier = TelegramNotifier()
        
        # ✅ ADD THESE ATTRIBUTES FOR TP/SL
        self.default_stop_loss_pips = 6    # 6 pips stop loss
        self.default_take_profit_pips = 9  # 9 pips take profit
    
    def _check_risk_management(self):
        """Check daily loss limit and drawdown"""
        try:
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
            
        except Exception as e:
            print(f"❌ Error in risk management check: {e}")
            return False
    
    def _check_max_positions(self):
        """Check maximum open positions"""
        try:
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
            
        except Exception as e:
            print(f"❌ Error checking max positions: {e}")
            return False
    
    def _calculate_position_size(self, symbol, price):
        """Calculate position size based on risk management"""
        try:
            risk_settings = self.config.get_risk_settings()
            account_info = mt5.account_info()
            
            if account_info is None:
                return 0.01  # default fallback
                
            # Risk per trade (0.75% of balance)
            risk_amount = account_info.balance * (risk_settings['max_daily_loss_percent'] / 100) / 3
            
            # Different settings for different instrument types
            if 'XAU' in symbol or 'GOLD' in symbol:
                # Gold - trade in units (0.01 = 0.01 oz)
                stop_loss_pips = 80  # Larger SL for gold
                pip_value = 0.01     # Approximate pip value for gold
                min_volume = 0.01    # Minimum volume for gold
                max_volume = 1.0     # Maximum volume for gold
            elif 'BTC' in symbol or 'ETH' in symbol:
                # Crypto - trade in units  
                stop_loss_pips = 150  # Even larger SL for crypto
                pip_value = 0.001     # Approximate pip value for crypto
                min_volume = 0.001    # Minimum volume for crypto
                max_volume = 0.1      # Maximum volume for crypto
            else:
                # Forex pairs - trade in lots
                stop_loss_pips = self.default_stop_loss_pips
                pip_value = 10        # Standard pip value for forex
                min_volume = 0.01     # Minimum lot size
                max_volume = 1.0      # Maximum lot size
            
            # Calculate position size
            position_size = risk_amount / (stop_loss_pips * pip_value)
            
            # Ensure minimum and maximum volume
            position_size = max(min_volume, min(position_size, max_volume))
            return round(position_size, 3)
            
        except Exception as e:
            print(f"❌ Error calculating position size: {e}")
            return 0.01  # fallback
    
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
                "deviation": 20,
                "magic": 2024,
                "comment": "AI Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Position closed: {position.symbol}")
                
                # Log the close trade
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
    
    def execute_trade(self, symbol, signal, lot_size=0.01):
        """Execute trade with Take Profit & Stop Loss"""
        try:
            if not self.mt5.connected:
                print("❌ Not connected to MT5")
                return False
                
            print(f"🔧 Starting trade execution for {symbol}...")
                
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
                
            print(f"🔧 Tick data - Bid: {tick.bid:.5f}, Ask: {tick.ask:.5f}")
                
            # Get account info for logging
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Cannot get account info")
                return False
                
            # Prepare order request
            if signal == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                # ✅ CALCULATE TP/SL FOR BUY
                stop_loss = price - (self.default_stop_loss_pips * 0.0001)  # 6 pips SL
                take_profit = price + (self.default_take_profit_pips * 0.0001)  # 9 pips TP
            elif signal == "SELL":
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                # ✅ CALCULATE TP/SL FOR SELL
                stop_loss = price + (self.default_stop_loss_pips * 0.0001)  # 6 pips SL
                take_profit = price - (self.default_take_profit_pips * 0.0001)  # 9 pips TP
            else:
                print("❌ Invalid signal")
                return False
                
            # Calculate position size based on risk
            lot_size = self._calculate_position_size(symbol, price)
            if lot_size <= 0:
                print("❌ Invalid position size")
                return False
                
            print(f"🔧 Trade Details:")
            print(f"   Symbol: {symbol}, Signal: {signal}")
            print(f"   Entry: {price:.5f}")
            print(f"   Stop Loss: {stop_loss:.5f} ({self.default_stop_loss_pips} pips)")
            print(f"   Take Profit: {take_profit:.5f} ({self.default_take_profit_pips} pips)")
            print(f"   Lot Size: {lot_size}")
            
            # Check symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                print(f"❌ Symbol {symbol} not found in MT5")
                return False
                
            # Create order request WITH TP/SL
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": stop_loss,        # ✅ STOP LOSS
                "tp": take_profit,      # ✅ TAKE PROFIT
                "deviation": 50,
                "magic": 2024,
                "comment": f"AI Scalping {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            print(f"🔧 Sending order request with TP/SL...")
            
            # Send order
            result = mt5.order_send(request)
            
            print(f"🔧 Order result - Retcode: {result.retcode}, Comment: {result.comment}")
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"❌ Order failed: {result.retcode} - {result.comment}")
                return False
                
            print(f"✅ Trade executed: {signal} {symbol} {lot_size} lots")
            print(f"   Entry: {price:.5f}")
            print(f"   Stop Loss: {stop_loss:.5f}")
            print(f"   Take Profit: {take_profit:.5f}")
            print(f"   Ticket: {result.order}")
            
            # ✅ TELEGRAM NOTIFICATION - Trade executed with TP/SL
            self.notifier.send_trade_notification(
                symbol=symbol,
                action=signal,
                price=price,
                volume=lot_size,
                ticket=result.order,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Track open position
            self.open_positions.append({
                'ticket': result.order,
                'symbol': symbol,
                'type': signal,
                'volume': lot_size,
                'open_price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'open_time': time.time()
            })
            
            # Log the trade
            trade_log_data = {
                'symbol': symbol,
                'signal': signal,
                'action': 'OPEN',
                'volume': lot_size,
                'entry_price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'ticket': result.order,
                'status': 'OPEN'
            }
            self.logger.log_trade(trade_log_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Trade execution error: {e}")
            import traceback
            traceback.print_exc()
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