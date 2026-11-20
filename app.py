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

import feedparser
from urllib.parse import quote
from google import genai

def pick_model(client):
    names = []
    for m in client.models.list():
        acts = getattr(m, "supported_actions", None) or []
        if "generateContent" in acts:
            names.append(m.name.replace("models/", ""))
    flash = sorted(n for n in names if "flash" in n
                   and not any(x in n for x in ["image", "tts", "live", "exp", "preview", "audio"]))
    if "gemini-2.5-flash" in flash:
        return "gemini-2.5-flash"
    return (flash or names)[-1]

st.divider()
st.subheader("Aaj ki khabron ka khulasa 📰")

TOPICS = {
    "Crypto": "bitcoin OR crypto market",
    "Gold aur Oil": "gold price OR oil price",
    "Forex": "forex dollar market",
}

@st.cache_data(ttl=3600)
def get_news(q):
    url = "https://news.google.com/rss/search?q=" + quote(q) + "&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    return [e.title for e in feed.entries[:8]]

@st.cache_data(ttl=3600)
def make_summary():
    lines = []
    for name, q in TOPICS.items():
        lines.append(name + ":")
        for t in get_news(q):
            lines.append("- " + t)
    prompt = (
        "Neeche market ki khabron ki headlines hain. "
        "Roman Urdu mein aasan alfaz mein khulasa likho: har topic ke liye 2-3 chhote nuqte. "
        "Koi trade ki salah ya qeemat ki peshgoi mat karna. "
        "Sirf headlines mein jo hai wo likho.\n\n" + "\n".join(lines)
    )
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    resp = client.models.generate_content(model=MODEL, contents=prompt)
    return resp.text

if st.button("News summary banao"):
    try:
        st.write(make_summary())
        st.caption("AI ka khulasa headlines par mabni hai, ghalat bhi ho sakta hai. Ye financial advice nahi.")
    except Exception as e:
        st.error("Summary nahi ban saki. Error ki pehli line mujhe bata dein.")
        st.code(str(e)[:200])
