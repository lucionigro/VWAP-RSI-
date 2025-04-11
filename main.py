from ib_insync import IB, Stock, util
import pandas as pd
import numpy as np
import ta  

def compute_vwap(df):
    """
    Calcula el VWAP acumulativo.
    VWAP = (suma acumulada de (precio * volumen)) / (suma acumulada del volumen)
    """
    df["vwap"] = (df['close'] * df['volume']).cumsum() / (df['volume'].cumsum())
    return df

def compute_rsi(df, period):
    """
    Calcula el RSI utilizando la librería ta.
    """
    rsi_indicator = ta.momentum.RSIIndicator(df['close'], window=period)
    return rsi_indicator.rsi()

def main():
    ib = IB()
    # Verificá el puerto configurado en TWS/IBG; aquí se usa 7496, pero puede variar si uso la paper acc
    ib.connect('127.0.0.1', 7496, clientId=1)
    
    tickers = ["AAPL", "MSFT", "INTC","COIN","V","CVX","NVDA","GOOGL","NU", "NIO", "TSLA","AMZN"]  
    contracts = [Stock(symbol, 'SMART', 'USD') for symbol in tickers]

    for contract in contracts:
        ib.qualifyContracts(contract)

    for contract in contracts:

        session_bars = ib.reqHistoricalData(
            contract,
            endDateTime='',      
            durationStr='1 D',
            barSizeSetting='5 mins',
            whatToShow='TRADES',
            useRTH=True,           
            formatDate=1
        )
        
        if not session_bars:
            print(f"No se pudieron obtener datos para {contract.symbol} (sesión)")
            continue

        # convertir a DataFrame y calcular VWAP de sesion
        df_session = util.df(session_bars)
        df_session = compute_vwap(df_session)
        
        # calcular RSI de 14 y 7 periodos para la sesion
        rsi_14 = compute_rsi(df_session, 14)
        rsi_7 = compute_rsi(df_session, 7)
        

        monthly_bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='30 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1
        )
        
        if not monthly_bars:
            print(f"No se pudieron obtener datos para {contract.symbol} (mensual)")
            continue

        df_monthly = util.df(monthly_bars)
        df_monthly = compute_vwap(df_monthly)
        

        current_session_vwap = df_session.iloc[-1]['vwap']
        current_price = df_session.iloc[-1]['close']
        current_monthly_vwap = df_monthly.iloc[-1]['vwap']
        current_rsi_14 = rsi_14.iloc[-1] 
        current_rsi_7 = rsi_7.iloc[-1]

        print(f"{contract.symbol}:")
        print(f"  - VWAP Sesión (5 mins): {current_session_vwap:.2f}")
        print(f"  - Precio actual: {current_price:.2f}")
        print(f"  - VWAP Mensual (últimos 30 días): {current_monthly_vwap:.2f}")
        print(f"  - RSI 14: {current_rsi_14:.2f}")
        print(f"  - RSI 7: {current_rsi_7:.2f}")

        # Alerta de compra: precio actual > VWAP de sesión
        if current_price > current_session_vwap:
            print(f"*** Alerta de COMPRA para {contract.symbol} ***")
        else:
            print(f"Sin alerta para {contract.symbol}")
        print("-" * 50)

    ib.disconnect()

if __name__ == "__main__":
    main()
