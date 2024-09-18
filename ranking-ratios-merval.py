import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Lista de tickers
tickers = ["GGAL.BA", "YPFD.BA", "PAMP.BA", "TXAR.BA", "ALUA.BA", "CRES.BA", "SUPV.BA", 
           "CEPU.BA", "BMA.BA", "TGSU2.BA", "TRAN.BA", "EDN.BA", "LOMA.BA", "MIRG.BA", 
           "DGCU2.BA", "BBAR.BA", "MOLI.BA", "TGNO4.BA", "CGPA2.BA", "COME.BA", "IRSA.BA", 
           "BYMA.BA", "TECO2.BA", "METR.BA", "CECO2.BA", "BHIP.BA", "AGRO.BA", "LEDE.BA", 
           "CVH.BA", "HAVA.BA", "AUSO.BA", "VALO.BA", "SEMI.BA", "INVJ.BA", "CTIO.BA", 
           "MORI.BA", "HARG.BA", "GCLA.BA", "SAMI.BA", "BOLT.BA", "MOLA.BA", "CAPX.BA", 
           "OEST.BA", "LONG.BA", "GCDI.BA", "GBAN.BA", "CELU.BA", "FERR.BA", "CADO.BA", 
           "GAMI.BA", "PATA.BA", "CARC.BA", "BPAT.BA", "RICH.BA", "INTR.BA", "GARO.BA", 
           "FIPL.BA", "GRIM.BA", "DYCA.BA", "POLL.BA", "DOME.BA", "ROSE.BA", "MTR.BA"]

# Aplicación de Streamlit
# Streamlit app
st.title("Stock Ratio Comparison")

# User input: ticker and start date
ticker_selected = st.selectbox("Selecciona un ticker:", tickers)
start_date = st.date_input("Selecciona una fecha de inicio:", value=datetime.today() - timedelta(days=365), 
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

# Adjust AGRO.BA prices for specific dates
def adjust_agro_ba_prices(stock_data):
    agro_ba_ticker = 'AGRO.BA'
    adjust_date = pd.Timestamp('2023-11-03')
    
    if agro_ba_ticker in stock_data.columns:
        # Multiply the value on November 3, 2023, by 2.1
        if adjust_date in stock_data.index:
            stock_data.loc[adjust_date, agro_ba_ticker] *= 2.1
        
        # Divide all values on or before November 2, 2023, by 6
        stock_data.loc[stock_data.index <= adjust_date - timedelta(days=1), agro_ba_ticker] /= 6
    
    return stock_data

# Download stock data
stock_data = get_stock_data(tickers, start_date)

# Apply the adjustments to AGRO.BA stock data
stock_data = adjust_agro_ba_prices(stock_data)

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

# Continue with the rest of your logic...


# Calcular ratios y cambios
if not stock_data.empty:
    # Obtener las fechas seleccionadas y la fecha actual (o la más cercana disponible)
    selected_date = get_closest_date(stock_data, start_date)
    today_date = get_closest_date(stock_data, datetime.today())

    if selected_date is not None and today_date is not None:
        st.write(f"Comparando ratios para {selected_date.date()} y {today_date.date()}")

        # Calcular los ratios
        selected_date_ratios = stock_data.loc[selected_date, ticker_selected] / stock_data.loc[selected_date]
        today_ratios = stock_data.loc[today_date, ticker_selected] / stock_data.loc[today_date]
        
        # Calcular el cambio porcentual en los ratios
        ratio_changes = (today_ratios - selected_date_ratios) / selected_date_ratios * 100
        ratio_changes = ratio_changes.drop(ticker_selected)

        # Combinar los resultados en un DataFrame
        results_df = pd.DataFrame({
            'Ratio Fecha Inicio': selected_date_ratios.drop(ticker_selected),
            'Ratio Fecha Final': today_ratios.drop(ticker_selected),
            'Cambio (Porcentaje)': ratio_changes
        })

        # Ordenar los ratios por cambio (de mayor a menor)
        ranked_results_df = results_df.sort_values(by='Cambio (Porcentaje)', ascending=False)
        
        # Mostrar los resultados
        st.write("### Valores de Ratios y Cambios:")
        st.dataframe(ranked_results_df)
        
        # Preparar datos para el gráfico de barras
        bar_plot_data = pd.DataFrame({
            'Ticker': ratio_changes.index,
            'Cambio (Porcentaje)': ratio_changes
        })

        # Permitir que el usuario seleccione qué barras mostrar
        selected_tickers = st.multiselect(
            "Seleccionar tickers a mostrar:",
            options=bar_plot_data['Ticker'],
            default=bar_plot_data['Ticker']
        )
        
        # Filtrar los datos según la selección del usuario
        filtered_bar_plot_data = bar_plot_data[bar_plot_data['Ticker'].isin(selected_tickers)]

        # Ordenar los datos filtrados por 'Cambio (Porcentaje)' en orden descendente
        sorted_bar_plot_data = filtered_bar_plot_data.sort_values(by='Cambio (Porcentaje)', ascending=False)

        # Crear gráfico de barras horizontales
        fig_bar = go.Figure(data=go.Bar(
            y=sorted_bar_plot_data['Ticker'],
            x=sorted_bar_plot_data['Cambio (Porcentaje)'],
            text=sorted_bar_plot_data['Cambio (Porcentaje)'].apply(lambda x: f"{x:.2f}%"),
            textposition='auto',
            marker=dict(color=sorted_bar_plot_data['Cambio (Porcentaje)'].apply(lambda x: 'red' if x < 0 else 'green')),
            orientation='h'
        ))

        fig_bar.update_layout(
            height=1200,
            yaxis_title='Tickers',
            xaxis_title='Cambio (Porcentaje)',
            title="Cambio Porcentual en Ratios",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(
                title='Cambio (Porcentaje)'
            ),
            yaxis=dict(title='Tickers'),
        )

        # Mostrar gráfico de barras horizontales
        st.plotly_chart(fig_bar)
    else:
        st.error("No hay datos válidos disponibles para la fecha seleccionada o la fecha actual.")
else:
    st.error("No hay datos disponibles para el rango de fechas seleccionado.")
