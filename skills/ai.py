import streamlit as st
from groq import Groq
from config import GROQ_KEY, GEMINI_KEY, GROQ_MODEL, GEMINI_MODEL, INDUSTRIES, MEMO_PROMPTS

groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

_gemini_client = None
if GEMINI_KEY and GEMINI_KEY != "your_gemini_api_key_here":
    try:
        from google import genai as _genai
        _gemini_client = _genai.Client(api_key=GEMINI_KEY)
    except Exception:
        pass


def groq_complete(prompt: str) -> str:
    resp = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content


def gemini_complete(prompt: str) -> str:
    resp = _gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return resp.text


def ai_complete(prompt: str) -> str:
    provider = st.session_state.get("ai_provider", "Groq")
    if provider == "Gemini" and _gemini_client:
        return gemini_complete(prompt)
    if groq_client:
        return groq_complete(prompt)
    raise RuntimeError("請先設定 GROQ_API_KEY 或 GEMINI_API_KEY")


def generate_memo(ticker: str, fmt: str, info: dict) -> str:
    price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
    prompt = f"""\
請根據以下資料，結合最新新聞與分析師觀點，為 {ticker} 撰寫投資備忘錄：

公司：{info.get("longName") or info.get("shortName", ticker)}
現價：{price}
52週高/低：{info.get("fiftyTwoWeekHigh","N/A")} / {info.get("fiftyTwoWeekLow","N/A")}
P/E：{info.get("trailingPE","N/A")}　EPS(TTM)：{info.get("trailingEps","N/A")}
毛利率：{info.get("grossMargins","N/A")}
目標價(共識)：{info.get("targetMeanPrice","N/A")}　評等：{info.get("recommendationKey","N/A")}
業務描述：{(info.get("longBusinessSummary") or "")[:400]}

{MEMO_PROMPTS[fmt]}
"""
    return ai_complete(prompt)


def classify_industry(name: str, description: str) -> str:
    prompt = (
        f"公司：{name}\n業務：{description[:200]}\n\n"
        f"從以下選項選最符合的產業（只回傳選項名稱，不要其他文字）：\n"
        + "、".join(INDUSTRIES)
    )
    result = ai_complete(prompt).strip()
    return result if result in INDUSTRIES else "其他"
