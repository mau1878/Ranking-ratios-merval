import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# List of tickers
tickers = ["GGAL.BA", "YPFD.BA", "PAMP.BA", "TXAR.BA", "ALUA.BA", "CRES.BA", "SUPV.BA", 
           "CEPU.BA", "BMA.BA", "TGSU2.BA", "TRAN.BA", "EDN.BA", "LOMA.BA", "MIRG.BA", 
           "DGCU2.BA", "BBAR.BA", "MOLI.BA", "TGNO4.BA", "CGPA2.BA", "COME.BA", "IRSA.BA", 
           "BYMA.BA", "TECO2.BA", "METR.BA", "CECO2.BA", "BHIP.BA", "AGRO.BA", "LEDE.BA", 
           "CVH.BA", "HAVA.BA", "AUSO.BA", "VALO.BA", "SEMI.BA", "INVJ.BA", "CTIO.BA", 
           "MORI.BA", "HARG.BA", "GCLA.BA", "SAMI.BA", "BOLT.BA", "MOLA.BA", "CAPX.BA", 
           "OEST.BA", "LONG.BA", "GCDI.BA", "GBAN.BA", "CELU.BA", "FERR.BA", "CADO.BA", 
           "GAMI.BA", "PATA.BA", "CARC.BA", "BPAT.BA", "RICH.BA", "INTR.BA", "GARO.BA", 
           "FIPL.BA", "GRIM.BA", "DYCA.BA", "POLL.BA", "DOME.BA", "ROSE.BA", "MTR.BA"]

# Streamlit app
st.title("Stock Ratio Comparison")

# User input: ticker and start date
ticker_selected = st.selectbox("Select a ticker:", tickers)
start_date = st.date_input("Select a start date:", value=datetime.today() - timedelta(days=365), 
                           min_value=datetime(2010, 1, 1), max_value=datetime.today())

# Fetch stock data
@st.cache_data
def get_stock_data(tickers, start_date):
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = start_date.strftime('%Y-%m-%d')
    stock_data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Adj Close']
    
    # Ensure index is in datetime format
    stock_data.index = pd.to_datetime(stock_data.index)
    
    return stock_data

# Download stock data
stock_data = get_stock_data(tickers, start_date)

# Function to get the closest available date for a given date
def get_closest_date(stock_data, date):
    # Ensure the index is in datetime format
    stock_data.index = pd.to_datetime(stock_data.index)
    
    # Make sure the date is timezone-aware (same timezone as stock_data.index)
    if pd.api.types.is_datetime64_any_dtype(stock_data.index):
        if stock_data.index.tz is not None:
            date = pd.Timestamp(date).tz_localize('UTC') if pd.Timestamp(date).tzinfo is None else pd.Timestamp(date)
        else:
            date = pd.Timestamp(date).tz_localize('UTC')
    
    # Compare and find the closest available date
    available_dates = stock_data.index[stock_data.index <= date]
    
    if not available_dates.empty:
        return available_dates[-1]

    return None # Return None if no valid previous date is found

# Calculate ratios and changes
if not stock_data.empty:
    # Get the dates for the selected date and today (or closest available)
    selected_date = get_closest_date(stock_data, start_date)
    today_date = get_closest_date(stock_data, datetime.today())

    if selected_date is not None and today_date is not None:
        st.write(f"Comparing ratios for {selected_date.date()} and {today_date.date()}")

        # Calculate the ratios
        selected_date_ratios = stock_data.loc[selected_date, ticker_selected] / stock_data.loc[selected_date]
        today_ratios = stock_data.loc[today_date, ticker_selected] / stock_data.loc[today_date]
        
        # Calculate the percentage change in ratios
        ratio_changes = (today_ratios - selected_date_ratios) / selected_date_ratios * 100
        ratio_changes = ratio_changes.drop(ticker_selected)  # Remove the selected ticker from the results

        # Combine results into a DataFrame
        results_df = pd.DataFrame({
            'Ratio Start Date': selected_date_ratios.drop(ticker_selected),
            'Ratio End Date': today_ratios.drop(ticker_selected),
            'Change (%)': ratio_changes
        })

        # Rank the ratios by change (decreasing)
        ranked_results_df = results_df.sort_values(by='Change (%)', ascending=False)
        
        # Display the results
        st.write("### Ratio Values and Changes:")
        st.dataframe(ranked_results_df)
        
        # Prepare data for the bar plot
        bar_plot_data = pd.DataFrame({
            'Ticker': ratio_changes.index,
            'Change (%)': ratio_changes
        })

        # Allow user to select which bars to display
        selected_tickers = st.multiselect(
            "Select tickers to display:",
            options=bar_plot_data['Ticker'],
            default=bar_plot_data['Ticker']
        )
        
        # Filter data based on user selection
        filtered_bar_plot_data = bar_plot_data[bar_plot_data['Ticker'].isin(selected_tickers)]

        # Create bar plot figure
        fig_bar = go.Figure(data=go.Bar(
            x=filtered_bar_plot_data['Ticker'],
            y=filtered_bar_plot_data['Change (%)'],
            text=filtered_bar_plot_data['Change (%)'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto',
            marker=dict(color=filtered_bar_plot_data['Change (%)'].apply(lambda x: 'red' if x < 0 else 'green'))
        ))

        fig_bar.update_layout(
            xaxis_title='Tickers',
            yaxis_title='Change (%)',
            title="Percentage Change in Ratios",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(tickangle=-45)  # Rotate x-axis labels for better visibility
        )

        # Display bar plot
        st.plotly_chart(fig_bar)
    else:
        st.error("No valid data available for the selected date or today.")
else:
    st.error("No data available for the selected date range.")
