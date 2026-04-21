import re
import json
import os
import requests
import yfinance as yf
import streamlit as st
from datetime import datetime
from config import CUSTOM_SYMBOLS_FILE

_TW_FUT_MONTH = {
    1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
    7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z",
}


@st.cache_data(ttl=86400)
def get_tw_stock_list() -> list[tuple[str, str]]:
    """每日更新一次的台股（上市＋上櫃＋興櫃）代號-名稱清單。"""
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    stocks: list[tuple[str, str]] = []

    _SOURCES = [
        # 上市 TWSE
        ("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
         "Code", "Name"),
        # 上櫃 TPEX
        ("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
         "SecuritiesCompanyCode", "CompanyName"),
        # 興櫃 TPEX ESB
        ("https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics",
         "SecuritiesCompanyCode", "CompanyName"),
    ]

    for url, code_field, name_field in _SOURCES:
        try:
            r = requests.get(url, timeout=10, verify=False)
            for item in r.json():
                code = item.get(code_field, "").strip()
                name = item.get(name_field, "").strip()
                if code.isdigit() and name and len(code) <= 5:
                    stocks.append((code, name))
        except Exception:
            pass

    return sorted(set(stocks))


def search_tw_stocks(query: str) -> list[tuple[str, str]]:
    """依代號前綴或名稱包含關鍵字篩選，最多回傳 8 筆。
    排序：4 位非 0 開頭（一般股票）→ 0 開頭 4 位（ETF）→ 5 位（新型 ETF）"""
    q = query.strip()
    if not q:
        return []
    results = [
        (code, name)
        for code, name in get_tw_stock_list()
        if code.startswith(q) or q in name
    ]
    results.sort(key=lambda x: (len(x[0]), x[0].startswith("0"), x[0]))
    return results[:8]


def load_custom_symbols() -> dict:
    if os.path.exists(CUSTOM_SYMBOLS_FILE):
        with open(CUSTOM_SYMBOLS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_custom_symbols(syms: dict):
    with open(CUSTOM_SYMBOLS_FILE, "w", encoding="utf-8") as f:
        json.dump(syms, f, ensure_ascii=False, indent=2)


def get_tw_futures_ticker() -> str | None:
    now = datetime.now()
    for offset in range(3):
        month = (now.month - 1 + offset) % 12 + 1
        year = now.year + (now.month - 1 + offset) // 12
        ticker = f"TWN-{_TW_FUT_MONTH[month]}{str(year)[-2:]}.SI"
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) >= 1:
                return ticker
        except Exception:
            pass
    return None


@st.cache_data(ttl=300)
def fetch_indices(symbols: tuple) -> dict:
    result = {}
    for name, sym in symbols:
        try:
            hist = yf.Ticker(sym).history(period="2d")
            if len(hist) >= 2:
                cur, prev = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
                result[name] = (cur, (cur - prev) / prev * 100)
            elif len(hist) == 1:
                result[name] = (hist["Close"].iloc[-1], None)
            else:
                result[name] = (None, None)
        except Exception:
            result[name] = (None, None)
    return result


@st.cache_data(ttl=600)
def get_stock_info(ticker: str) -> dict:
    return yf.Ticker(ticker).info


def resolve_ticker(query: str) -> str:
    from skills.ai import ai_complete, groq_client, _gemini_client

    q = query.strip()

    # 純數字 → 台股
    if q.isdigit():
        return q + ".TW"

    # 已是合法 ticker 格式（全大寫英數 + 選擇性交易所後綴）
    if re.match(r'^[A-Z0-9]+(\.[A-Za-z]{1,3})?$', q):
        return q

    # 先查本地台股清單（精確名稱比對）
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', q))
    if has_chinese:
        tw_hits = search_tw_stocks(q)
        if len(tw_hits) == 1:
            return tw_hits[0][0] + ".TW"
        if tw_hits and tw_hits[0][1] == q:      # 完全相符取第一筆
            return tw_hits[0][0] + ".TW"

    # yfinance Search（英文 / 中文都嘗試）
    try:
        results = yf.Search(q, max_results=10).quotes
        equities = [x for x in results if x.get("quoteType") == "EQUITY"]
        preferred = [x for x in equities if x.get("exchDisp", "") in
                     ("NASDAQ", "NYSE", "NasdaqGS", "NasdaqGM", "Taiwan")]
        best = preferred[0] if preferred else (equities[0] if equities else None)
        if best:
            return best["symbol"]
    except Exception:
        pass

    # AI 補足：明確說明台股格式
    if groq_client or _gemini_client:
        result = ai_complete(
            f"請將以下公司名稱轉換為 Yahoo Finance 股票代號，只回傳代號，不含任何其他文字。\n"
            f"規則：台灣上市/上櫃股票必須加 .TW 後綴（例：台積電→2330.TW、聯發科→2454.TW、鴻海→2317.TW）；"
            f"美股直接回傳代號（例：NVDA、AAPL、TSLA）。\n"
            f"公司名稱：{q}"
        ).strip().split()[0]
        return result

    return q
