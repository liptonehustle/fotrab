import pandas as pd
import json
import os
from datetime import datetime

class LogAnalyzer:
    def __init__(self):
        self.log_dir = "logs"
    
    def generate_summary_report(self):
        """Generate comprehensive summary report from logs"""
        print("📊 GENERATING TRADING SUMMARY REPORT...")
        print("=" * 60)
        
        summary = {
            'overview': self._get_overview(),
            'performance': self._get_performance_metrics(),
            'strategy_analysis': self._get_strategy_analysis(),
            'pairs_analysis': self._get_pairs_analysis(),
            'issues_recommendations': self._get_issues_and_recommendations()
        }
        
        self._print_summary(summary)
        return summary
    
    def _get_overview(self):
        """Get basic overview of trading activity"""
        overview = {}
        
        # Trades data
        try:
            trades_df = pd.read_csv(f'{self.log_dir}/trades.csv')
            overview['total_trades'] = len(trades_df)
            overview['open_trades'] = len(trades_df[trades_df['status'] == 'OPEN'])
            overview['closed_trades'] = len(trades_df[trades_df['status'] == 'CLOSED'])
            
            if not trades_df.empty:
                overview['first_trade'] = trades_df.iloc[0]['timestamp']
                overview['last_trade'] = trades_df.iloc[-1]['timestamp']
        except FileNotFoundError:
            overview['total_trades'] = 0
            overview['error'] = 'No trades data found'
        
        # Signals data
        try:
            signals_df = pd.read_csv(f'{self.log_dir}/signals.csv')
            overview['total_signals'] = len(signals_df)
            overview['buy_signals'] = len(signals_df[signals_df['signal'] == 'BUY'])
            overview['sell_signals'] = len(signals_df[signals_df['signal'] == 'SELL'])
            overview['no_signals'] = len(signals_df[signals_df['signal'] == 'NO_SIGNAL'])
        except FileNotFoundError:
            overview['total_signals'] = 0
        
        return overview
    
    def _get_performance_metrics(self):
        """Calculate performance metrics"""
        performance = {}
        
        try:
            trades_df = pd.read_csv(f'{self.log_dir}/trades.csv')
            
            if trades_df.empty:
                return {'error': 'No trades data'}
            
            # Basic metrics
            closed_trades = trades_df[trades_df['status'] == 'CLOSED']
            if not closed_trades.empty:
                performance['total_profit'] = closed_trades['profit'].sum()
                performance['winning_trades'] = len(closed_trades[closed_trades['profit'] > 0])
                performance['losing_trades'] = len(closed_trades[closed_trades['profit'] < 0])
                performance['total_trades_closed'] = len(closed_trades)
                
                if performance['total_trades_closed'] > 0:
                    performance['win_rate'] = (performance['winning_trades'] / performance['total_trades_closed']) * 100
                    performance['avg_profit_per_trade'] = performance['total_profit'] / performance['total_trades_closed']
                else:
                    performance['win_rate'] = 0
                    performance['avg_profit_per_trade'] = 0
            else:
                performance['total_trades_closed'] = 0
                performance['win_rate'] = 0
                performance['total_profit'] = 0
            
            # Risk metrics
            if 'balance' in trades_df.columns:
                performance['peak_balance'] = trades_df['balance'].max()
                performance['lowest_balance'] = trades_df['balance'].min()
                if performance['peak_balance'] > 0:
                    performance['max_drawdown'] = ((performance['peak_balance'] - performance['lowest_balance']) / performance['peak_balance']) * 100
                else:
                    performance['max_drawdown'] = 0
            
        except Exception as e:
            performance['error'] = f'Error calculating performance: {e}'
        
        return performance
    
    def _get_strategy_analysis(self):
        """Analyze strategy effectiveness"""
        strategy = {}
        
        try:
            signals_df = pd.read_csv(f'{self.log_dir}/signals.csv')
            trades_df = pd.read_csv(f'{self.log_dir}/trades.csv')
            
            if signals_df.empty:
                return {'error': 'No signals data'}
            
            # Signal effectiveness
            buy_signals = signals_df[signals_df['signal'] == 'BUY']
            sell_signals = signals_df[signals_df['signal'] == 'SELL']
            
            strategy['total_buy_signals'] = len(buy_signals)
            strategy['total_sell_signals'] = len(sell_signals)
            strategy['signal_ratio'] = f"{len(buy_signals)}:{len(sell_signals)}"
            
            # Indicator analysis (if available)
            if 'rsi' in signals_df.columns:
                strategy['avg_rsi_buy'] = buy_signals['rsi'].mean() if not buy_signals.empty else 0
                strategy['avg_rsi_sell'] = sell_signals['rsi'].mean() if not sell_signals.empty else 0
            
        except Exception as e:
            strategy['error'] = f'Error in strategy analysis: {e}'
        
        return strategy
    
    def _get_pairs_analysis(self):
        """Analyze performance by trading pair"""
        pairs_analysis = {}
        
        try:
            trades_df = pd.read_csv(f'{self.log_dir}/trades.csv')
            
            if trades_df.empty:
                return {'error': 'No trades data'}
            
            # Group by symbol
            for symbol in trades_df['symbol'].unique():
                symbol_trades = trades_df[trades_df['symbol'] == symbol]
                closed_trades = symbol_trades[symbol_trades['status'] == 'CLOSED']
                
                pairs_analysis[symbol] = {
                    'total_trades': len(symbol_trades),
                    'closed_trades': len(closed_trades),
                    'open_trades': len(symbol_trades[symbol_trades['status'] == 'OPEN']),
                    'total_profit': closed_trades['profit'].sum() if not closed_trades.empty else 0,
                    'win_rate': (len(closed_trades[closed_trades['profit'] > 0]) / len(closed_trades) * 100) if len(closed_trades) > 0 else 0
                }
            
        except Exception as e:
            pairs_analysis['error'] = f'Error in pairs analysis: {e}'
        
        return pairs_analysis
    
    def _get_issues_and_recommendations(self):
        """Identify issues and provide recommendations"""
        issues = []
        recommendations = []
        
        try:
            trades_df = pd.read_csv(f'{self.log_dir}/trades.csv')
            signals_df = pd.read_csv(f'{self.log_dir}/signals.csv')
            
            # Check for issues
            if len(trades_df) == 0:
                issues.append("❌ No trades executed - check strategy or execution")
                recommendations.append("✅ Review strategy parameters and ensure symbols are available")
            
            if len(signals_df) > 0 and len(trades_df) == 0:
                issues.append("⚠️ Signals generated but no trades executed")
                recommendations.append("✅ Check trade execution - possible symbol selection or account permission issues")
            
            # Check win rate if we have closed trades
            closed_trades = trades_df[trades_df['status'] == 'CLOSED']
            if len(closed_trades) > 0:
                win_rate = (len(closed_trades[closed_trades['profit'] > 0]) / len(closed_trades)) * 100
                if win_rate < 40:
                    issues.append(f"⚠️ Low win rate: {win_rate:.1f}%")
                    recommendations.append("✅ Consider adjusting strategy parameters or adding more confirmation indicators")
                elif win_rate > 70:
                    issues.append(f"🎉 High win rate: {win_rate:.1f}% - Good job!")
            
            # Check for open positions
            open_trades = trades_df[trades_df['status'] == 'OPEN']
            if len(open_trades) > 0:
                issues.append(f"ℹ️ {len(open_trades)} open positions need management")
                recommendations.append("✅ Ensure position management is working properly")
                
        except Exception as e:
            issues.append(f"❌ Error analyzing issues: {e}")
        
        return {
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _print_summary(self, summary):
        """Print formatted summary report"""
        print("\n📈 TRADING PERFORMANCE SUMMARY")
        print("=" * 50)
        
        # Overview
        overview = summary['overview']
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Trades: {overview.get('total_trades', 0)}")
        print(f"   - Open: {overview.get('open_trades', 0)}")
        print(f"   - Closed: {overview.get('closed_trades', 0)}")
        print(f"   Total Signals: {overview.get('total_signals', 0)}")
        print(f"   - BUY: {overview.get('buy_signals', 0)}")
        print(f"   - SELL: {overview.get('sell_signals', 0)}")
        print(f"   - NO_SIGNAL: {overview.get('no_signals', 0)}")
        
        # Performance
        performance = summary['performance']
        print(f"\n💰 PERFORMANCE:")
        if 'error' not in performance:
            print(f"   Total Profit: ${performance.get('total_profit', 0):.2f}")
            print(f"   Win Rate: {performance.get('win_rate', 0):.1f}%")
            print(f"   Avg Profit/Trade: ${performance.get('avg_profit_per_trade', 0):.2f}")
            print(f"   Max Drawdown: {performance.get('max_drawdown', 0):.1f}%")
        else:
            print(f"   {performance['error']}")
        
        # Pairs Analysis
        pairs = summary['pairs_analysis']
        print(f"\n🎯 PAIRS PERFORMANCE:")
        if 'error' not in pairs:
            for symbol, data in pairs.items():
                if symbol != 'error':
                    print(f"   {symbol}: {data['total_trades']} trades, "
                          f"Win Rate: {data['win_rate']:.1f}%, "
                          f"Profit: ${data['total_profit']:.2f}")
        else:
            print(f"   {pairs['error']}")
        
        # Issues & Recommendations
        issues_rec = summary['issues_recommendations']
        print(f"\n🔧 ISSUES & RECOMMENDATIONS:")
        for issue in issues_rec['issues']:
            print(f"   {issue}")
        for rec in issues_rec['recommendations']:
            print(f"   {rec}")
        
        print("\n" + "=" * 50)
        print("📋 Share this summary for further analysis!")

def main():
    analyzer = LogAnalyzer()
    analyzer.generate_summary_report()

if __name__ == "__main__":
    main()