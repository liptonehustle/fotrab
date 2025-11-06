import MetaTrader5 as mt5
import time
from datetime import datetime, timedelta
from config.settings import Config

class PositionManager:
    def __init__(self, mt5_connector, trade_executor):
        self.mt5 = mt5_connector
        self.executor = trade_executor
        self.config = Config()
        
    def manage_open_positions(self):
        """Manage all open positions - take profit & stop loss"""
        try:
            if not self.mt5.connected:
                return
                
            positions = mt5.positions_get()
            if not positions:
                return
                
            print(f"🔍 Managing {len(positions)} open positions...")
            
            for position in positions:
                self._check_position_management(position)
                
        except Exception as e:
            print(f"❌ Error managing positions: {e}")
    
    def _check_position_management(self, position):
        """Check individual position for manual TP/SL if MT5 TP/SL fails"""
        symbol = position.symbol
        current_time = time.time()
        position_age = current_time - position.time
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return
            
        if position.type == mt5.ORDER_TYPE_BUY:
            current_price = tick.bid
            profit = (current_price - position.price_open) * position.volume * 100000
        else:  # SELL
            current_price = tick.ask  
            profit = (position.price_open - current_price) * position.volume * 100000
        
        profit_pips = profit / (position.volume * 10)
        
        print(f"  {symbol} {('BUY' if position.type == 0 else 'SELL')}: "
            f"Profit: {profit_pips:.1f} pips, Age: {position_age/60:.1f} min")
        
        # ✅ MANUAL TAKE PROFIT (if MT5 TP doesn't work)
        if profit_pips >= 9:  # 9 pips profit
            print(f"🎯 Manual Take Profit hit for {symbol} (+{profit_pips:.1f}pips)")
            self.executor.close_position(position.ticket)
            return
            
        # ✅ MANUAL STOP LOSS (if MT5 SL doesn't work)  
        if profit_pips <= -6:  # 6 pips loss
            print(f"🛑 Manual Stop Loss hit for {symbol} ({profit_pips:.1f}pips)")
            self.executor.close_position(position.ticket)
            return
            
        # ✅ TIME-BASED CLOSE (max 30 minutes for scalping)
        if position_age > 1800:  # 30 minutes
            print(f"⏰ Time-based close for {symbol} (30+ minutes)")
            self.executor.close_position(position.ticket)
            return
    
def get_position_summary(self):
    """Get summary of all open positions"""
    try:
        positions = mt5.positions_get()
        if not positions:
            return {
                'total_positions': 0,
                'total_profit_usd': 0,
                'positions': []
            }  # ✅ Return dict instead of string
            
        summary = []
        total_profit = 0
        
        for position in positions:
            tick = mt5.symbol_info_tick(position.symbol)
            if tick:
                if position.type == mt5.ORDER_TYPE_BUY:
                    profit = (tick.bid - position.price_open) * position.volume * 100000
                else:
                    profit = (position.price_open - tick.ask) * position.volume * 100000
                
                total_profit += profit
                profit_pips = profit / (position.volume * 10)
                
                summary.append({
                    'symbol': position.symbol,
                    'type': 'BUY' if position.type == 0 else 'SELL',
                    'volume': position.volume,
                    'open_price': position.price_open,
                    'current_price': tick.bid if position.type == 0 else tick.ask,
                    'profit_pips': profit_pips,
                    'profit_usd': profit,
                    'age_minutes': (time.time() - position.time) / 60
                })
        
        return {
            'total_positions': len(positions),
            'total_profit_usd': total_profit,
            'positions': summary
        }
        
    except Exception as e:
        print(f"❌ Error getting position summary: {e}")
        return {
            'total_positions': 0,
            'total_profit_usd': 0,
            'positions': []
        }  # ✅ Return empty dict on error

# Test function
def test_position_manager():
    from core.mt5_connector import MT5Connector
    from core.trade_executor import TradeExecutor
    
    print("Testing Position Manager...")
    connector = MT5Connector()
    
    if connector.connect():
        executor = TradeExecutor(connector)
        manager = PositionManager(connector, executor)
        
        # Get position summary
        summary = manager.get_position_summary()
        if summary:
            print(f"Open Positions: {summary['total_positions']}")
            for pos in summary['positions']:
                print(f"  {pos['symbol']} {pos['type']}: {pos['profit_pips']:.1f} pips")
        
        # Manage positions
        manager.manage_open_positions()
        
        connector.disconnect()

if __name__ == "__main__":
    test_position_manager()