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
        ranked_results_df = results_df.sort_values(by='Change (%)', ascending=True)
        
        # Display the results
        st.write("### Ratio Values and Changes:")
        st.dataframe(ranked_results_df)
        
        # Prepare data for the heatmap
        heatmap_data = pd.DataFrame({
            'Ticker': ratio_changes.index,
            'Change (%)': ratio_changes
        })

        # Create a matrix for heatmap
        heatmap_matrix = pd.DataFrame(heatmap_data['Change (%)'].values.reshape(1, -1), 
                                      columns=heatmap_data['Ticker'])

        # Create heatmap figure
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_matrix.values,
            x=heatmap_matrix.columns,
            y=[0],  # Single row to align labels vertically
            colorscale='Viridis',
            colorbar=dict(title='Change (%)'),
            zmin=heatmap_data['Change (%)'].min(),
            zmax=heatmap_data['Change (%)'].max()
        ))

        # Add ticker names inside each cell
        for i, ticker in enumerate(heatmap_data['Ticker']):
            fig_heatmap.add_trace(go.Scatter(
                x=[ticker],
                y=[0],
                text=[ticker],
                mode='text',
                textfont=dict(size=12, color='white'),
                showlegend=False
            ))

        fig_heatmap.update_layout(
            xaxis_title='Tickers',
            yaxis_title='',
            yaxis=dict(showgrid=False, showticklabels=False),
            xaxis=dict(tickmode='array', tickvals=heatmap_data['Ticker']),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            title="Squared Heatmap of Ratio Changes"
        )

        # Display heatmap
        st.plotly_chart(fig_heatmap)
    else:
        st.error("No valid data available for the selected date or today.")
else:
    st.error("No data available for the selected date range.")
