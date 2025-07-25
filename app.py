
import streamlit as st # for interface

import plotly as pl # for graphs

from datetime import datetime # for data

import yfinance as yf # stocks and forex

import pandas_ta as ta # indicators

import plotly as pl # graphs
import plotly.graph_objects as go # graphs

st.title('QuantSight Backtester Lite')

# Asset selection method
def hist_data():

    asset = st.selectbox('Select asset type', ['Stocks'], 
                         help = 'Forex and Crypto in full version ;)')

        # stocks
    if asset == 'Stocks':
        ticker = yf.Ticker('AAPL')
            
        interval_main = st.selectbox('Over 1 day Interval', ['Over 1 day', 'Under 1 day'])
            
        if interval_main == 'Over 1 day':
            stock_start_date = st.text_input('Start date', value = 'YYYY-MM-DD')
            stock_end_date = st.text_input('Ends date', value = 'YYYY-MM-DD')

            interval = st.selectbox('What interval would you like?', ['1d', '1wk', '1mo'])

            start_date = datetime.strptime(stock_start_date, '%Y-%m-%d')
            end_date = datetime.strptime(stock_end_date, '%Y-%m-%d')

            stock_data = ticker.history(start = start_date, end = end_date, interval = interval)
            return stock_data
            
        elif interval_main == 'Under 1 day':
            period = st.text_input('Choose a period (please input in days, or max for alltime)', value = '50d')
            interval = st.selectbox('Select an interval',
                                      ['1m', '5m', '15m', '30m', '60m','90m'], 
                                      help = '1m: Max 7 days, 2m - 15m: Up to 60 days, 60m: Up to 730 days, 90m: Up to 60 days')

            stock_data = ticker.history(period = period, interval = interval)
            return stock_data
    
    return stock_data

data = hist_data()


# strategies    

def strategies():
    str_options = {
        "RSI overbought/oversold": rsi_overboughtoversold,
    }
    
    # Pass only keys (strategy names) as options
    selected_names = st.multiselect('Select one or more options below', list(str_options.keys()))
    
    # Return list of functions for selected strategy names
    selected_funcs = [str_options[name] for name in selected_names]
    
    return selected_funcs

        
def rsi_overboughtoversold(data):
    
    rsi_length = st.select_slider('Select RSI length', options = [5, 7, 10, 14, 21, 28], value = 14)
    overbought = st.slider('Overbought threshold', min_value = 60, max_value = 90, value = 70)
    oversold = st.slider('Oversold threshold', min_value = 10, max_value = 40, value = 30)

    rsi_trade_type = st.radio('Trade entry condition', ['On cross', 'On touch'])

    take_profit = st.slider('Take profit percentage', min_value = 1, max_value = 100, value = 10) / 100
    stop_loss = st.slider('Stop loss percentage', min_value = 1, max_value = 100, value = 5) / 100 

    in_position = False
    entry_price = 0
    trades = []
    entry_time = None

    data['RSI'] = ta.rsi(data['Close'], length = rsi_length)

    data['Signal'] = ''

    for i in range(len(data)):
        if i == 0:
            continue
        price = data['Close'].iloc[i]
        rsi = data['RSI'].iloc[i]

        if not in_position:
            if rsi_trade_type == 'On touch' and rsi < oversold:

                # buy signal
                in_position = True
                entry_price = price
                entry_time = data.index[i]
                data.at[data.index[i], 'Signal'] = 'Buy (Touch)'

            elif rsi_trade_type == 'On cross' and data['RSI'].iloc[i-1] < oversold and rsi > oversold:
                in_position = True
                entry_price = price
                entry_time = data.index[i]
                data.at[data.index[i], 'Signal'] = 'Buy (Cross)'

        elif in_position:
            if price >= entry_price * (1 + take_profit):
                in_position = False
                data.at[data.index[i], 'Signal'] = 'Sell (Take profit)'
                trades.append({
                'Entry Time': entry_time,
                'Exit Time': data.index[i],
                'Entry Price': entry_price,
                'Exit Price': price,
                'P&L': price - entry_price
            })
                
            elif price <= entry_price * (1 - stop_loss):
                in_position = False
                data.at[data.index[i], 'Signal'] = 'Sell (Stop loss)'
                trades.append({
                'Entry Time': entry_time,
                'Exit Time': data.index[i],
                'Entry Price': entry_price,
                'Exit Price': price,
                'P&L': price - entry_price
            })
                
            elif rsi_trade_type == 'On cross' and data['RSI'].iloc[i-1] > overbought and rsi < overbought:
                in_position = False
                data.at[data.index[i], 'Signal'] = 'Sell (Cross)'
                trades.append({
                'Entry Time': entry_time,
                'Exit Time': data.index[i],
                'Entry Price': entry_price,
                'Exit Price': price,
                'P&L': price - entry_price
            })
                
            elif rsi_trade_type == 'On touch' and rsi > overbought:
                in_position = False
                data.at[data.index[i], 'Signal'] = 'Sell (Touch)'
                trades.append({
                'Entry Time': entry_time,
                'Exit Time': data.index[i],
                'Entry Price': entry_price,
                'Exit Price': price,
                'P&L': price - entry_price
            })
                
    return data, trades    

def plot_trade_chart(data, trades, title='Backtest result'):
    fig = go.Figure()

    # Price candlestick
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ))

    for trade in trades:
        # Buy marker
        fig.add_trace(go.Scatter(
            x=[trade['Entry Time']],
            y=[trade['Entry Price']],
            mode='markers+text',
            marker=dict(symbol='triangle-up', color='green', size=12),
            text=['Buy'],
            textposition='top center',
            name='Buy'
        ))

        # Sell marker
        fig.add_trace(go.Scatter(
            x=[trade['Exit Time']],
            y=[trade['Exit Price']],
            mode='markers+text',
            marker=dict(symbol='triangle-down', color='red', size=12),
            text=[f"P&L: {trade['P&L']:.2f}"],
            textposition='bottom center',
            name='Sell'
        ))

    # Layout
    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x unified',
        template='plotly_dark'
    )

    st.plotly_chart(fig, use_container_width = True)  

    #return fig
