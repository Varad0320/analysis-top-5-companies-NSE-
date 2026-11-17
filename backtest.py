import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. Load the raw CSV and extract only the actual trading rows (starting from row 14)
raw = pd.read_csv('nse_top5.csv', skiprows=14)

# Keep only the 6 relevant columns (Columns 1 to 6) and drop empty spacer rows
df = raw.iloc[:, 1:7].copy()
df.columns = ['Date', 'RELIANCE', 'TCS', 'HDFCBANK', 'BHARTIARTL', 'ICICIBANK']
df = df.dropna(subset=['Date'])
df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date').sort_index()

# Clean '₹' and commas so Python reads them as real numbers
stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'BHARTIARTL', 'ICICIBANK']
for stock in stocks:
    df[stock] = df[stock].astype(str).str.replace('₹', '', regex=False).str.replace(',', '', regex=False).astype(float)

summary_results = []
plt.figure(figsize=(12, 6))

# 2. Run the 5-Day Moving Average Momentum Strategy across all 5 stocks
for stock in stocks:
    data = pd.DataFrame(index=df.index)
    data['Close'] = df[stock]
    
    # 5-Day Simple Moving Average (1 trading week)
    data['SMA_5'] = data['Close'].rolling(window=5).mean()
    
    # Signal: 1 = Buy/Hold when price > 5-day SMA, 0 = Exit to Cash
    data['Signal'] = np.where(data['Close'] > data['SMA_5'], 1, 0)
    
    # Shift by 1 day to prevent look-ahead bias
    data['Position'] = data['Signal'].shift(1).fillna(0)
    
    # Daily returns + 2% daily stop-loss risk cap
    data['Market_Return'] = data['Close'].pct_change().fillna(0)
    data['Strategy_Return'] = (data['Market_Return'] * data['Position']).clip(lower=-0.02)
    
    # Cumulative Returns
    data['Cum_Market'] = (1 + data['Market_Return']).cumprod()
    data['Cum_Strategy'] = (1 + data['Strategy_Return']).cumprod()
    
    # Annualized Sharpe Ratio & Max Drawdown
    trading_days = 252
    risk_free_rate = 0.065
    excess_ret = data['Strategy_Return'] - (risk_free_rate / trading_days)
    sharpe = np.sqrt(trading_days) * (excess_ret.mean() / (data['Strategy_Return'].std() + 1e-9))
    
    rolling_max = data['Cum_Strategy'].cummax()
    drawdown = (data['Cum_Strategy'] - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    summary_results.append({
        'Ticker': stock,
        'Strategy Return (%)': round((data['Cum_Strategy'].iloc[-1] - 1) * 100, 2),
        'Buy & Hold Return (%)': round((data['Cum_Market'].iloc[-1] - 1) * 100, 2),
        'Sharpe Ratio': round(sharpe, 2),
        'Max Drawdown (%)': round(max_drawdown * 100, 2)
    })
    
    plt.plot(data.index, data['Cum_Strategy'], marker='o', label=f'{stock} Strategy')

# 3. Print & Save Results
results_df = pd.DataFrame(summary_results)
print("\n=== 14-DAY NSE BACKTEST SUMMARY (5-DAY SMA) ===")
print(results_df.to_string(index=False))
results_df.to_csv('backtest_summary.csv', index=False)

plt.title('5-Day Momentum Strategy: Cumulative Equity Curves (14 Trading Days)')
plt.xlabel('Trading Date')
plt.ylabel('Portfolio Growth (1.0 = Initial Capital)')
plt.xticks(rotation=45)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('equity_curves.png', dpi=300)
plt.show()
