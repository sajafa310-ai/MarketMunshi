import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="MarketMunshi", layout="wide")
st.title("MarketMunshi 📊")
st.caption("Research aur alert assistant. Ye financial advice nahi hai.")

ITEMS = {
    "Crypto": ["BTC-USD","ETH-USD","SOL-USD","XRP-USD","ADA-USD","LTC-USD",
               "DOT-USD","LINK-USD","AVAX-USD","DOGE-USD","ATOM-USD"],
    "Commodity": ["GC=F","SI=F","CL=F","BZ=F"],
    "Forex": ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X"],
}

@st.cache_data(ttl=3600)
def scan():
    rows = []
    for grp, syms in ITEMS.items():
        for p in syms:
            try:
                raw = yf.download(p, period="6mo", interval="1d",
                                  progress=False, auto_adjust=True)
                c = raw["Close"].squeeze().dropna()
                delta = c.diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rsi = 100 - 100 / (1 + gain / loss)
                trend_up = c.iloc[-1] > c.rolling(50).mean().iloc[-1]
                sig = (rsi.iloc[-1] < 30) and trend_up
                rows.append([grp, p, round(float(c.iloc[-1]), 4),
                             round(float(rsi.iloc[-1]), 1),
                             "UPAR" if trend_up else "NEECHE",
                             "SIGNAL" if sig else "-"])
            except Exception:
                rows.append([grp, p, None, None, None, "skip"])
    return pd.DataFrame(rows, columns=["Group","Symbol","Price","RSI","Trend","Alert"])

if st.button("Refresh"):
    st.cache_data.clear()
    st.rerun()

df = scan()
n = int((df["Alert"] == "SIGNAL").sum())
if n:
    st.success(f"Aaj {n} signal bana hai")
else:
    st.info("Aaj koi signal nahi (rule: RSI < 30 aur trend upar)")

st.dataframe(df)
st.caption("Backtest ka khulasa: crypto mein ishara, commodity mein kamzor ishara, forex mein koi edge nahi. Rule abhi sirf candidate hai.")
