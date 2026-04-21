import streamlit as st
from datetime import datetime, timedelta

from config import GROQ_KEY, GEMINI_KEY, NOTION_TOKEN, SJ_API_KEY, DEFAULT_SYMBOLS, MEMO_PROMPTS
from skills.ai import groq_client, _gemini_client, ai_complete, generate_memo
from skills.market import (
    get_tw_futures_ticker, fetch_indices, load_custom_symbols,
    save_custom_symbols, resolve_ticker, get_stock_info, search_tw_stocks,
)
from skills.macromicro import fetch_mm_quickie
from skills.youtube import fetch_youtube_transcript
from skills.shioaji_account import (
    get_sj_api, fetch_sj_tw_snapshot,
    fetch_sj_stock_positions, fetch_sj_futopt_positions, fetch_sj_balance,
)
from skills.notion_push import push_to_notion
from skills.storage import load_briefings, save_briefing

st.set_page_config(page_title="個人研究台", page_icon="🧑🏻‍💻", layout="wide")

st.title("🧑🏻‍💻 個人研究台")
st.caption("研究工具")

tab_morning, tab_memo, tab_account = st.tabs(["☀️ 晨報", "📝 備忘錄", "📈 帳戶"])

# ── 晨報 ──────────────────────────────────────────────────
with tab_morning:
    st.subheader("市場快照")

    if st.button("Press Cmd+R to Restart..."):
        st.cache_data.clear()
        st.rerun()

    _tw_fut = get_tw_futures_ticker()
    _all_syms: dict[str, str] = {}
    for name, sym in DEFAULT_SYMBOLS.items():
        if name == "台指期近":
            if _tw_fut:
                _all_syms[name] = _tw_fut
        else:
            _all_syms[name] = sym
    _all_syms.update(load_custom_symbols())

    data = fetch_indices(tuple(_all_syms.items()))

    _sj = get_sj_api()
    if _sj:
        try:
            data.update(fetch_sj_tw_snapshot(_sj))
        except Exception:
            pass

    _COL_N = 6
    _items = list(data.items())
    for _row_start in range(0, len(_items), _COL_N):
        _row = _items[_row_start:_row_start + _COL_N]
        _cols = st.columns(len(_row))
        for _col, (_name, (_price, _chg)) in zip(_cols, _row):
            if _price is not None:
                _fmt = f"{_price:,.0f}" if _price >= 100 else f"{_price:,.2f}"
                _delta = f"{_chg:+.2f}%" if _chg is not None else ""
                _col.metric(_name, _fmt, _delta)
            else:
                _col.metric(_name, "—", "")

    with st.expander("➕管理自訂標的"):
        _custom = load_custom_symbols()
        if _custom:
            _to_del = st.multiselect("選擇要移除的標的", list(_custom.keys()), key="del_sym")
            if st.button("移除", key="btn_del") and _to_del:
                for _k in _to_del:
                    _custom.pop(_k, None)
                save_custom_symbols(_custom)
                st.cache_data.clear()
                st.rerun()
        _c1, _c2, _c3 = st.columns([2, 2, 1])
        _new_name = _c1.text_input("新增標的", placeholder="EX：台積電", key="sym_name")
        _new_sym  = _c2.text_input("輸入Yahoo Finance 代號", placeholder="EX：NVDA", key="sym_ticker")
        if _c3.button("加入", key="btn_add"):
            if _new_name and _new_sym:
                _custom[_new_name] = _new_sym.upper()
                save_custom_symbols(_custom)
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("請填寫名稱與代號")

    st.divider()

    st.subheader("📰 MM 每日短評")
    today_str = datetime.now().strftime("%Y-%m-%d")
    with st.spinner("載入中..."):
        mm_posts = fetch_mm_quickie()

    _today_mm = [p for p in mm_posts if p.get("date") == today_str]
    _display_mm = _today_mm if _today_mm else mm_posts
    if not _today_mm and mm_posts and mm_posts[0].get("date"):
        st.caption(f"今日無新短評，顯示最近一期（{mm_posts[0]['date']}）")

    for post in _display_mm:
        label = f"{post['title']} · {post['date']}" if post['date'] else post['title']
        with st.expander(label):
            if post.get("content"):
                st.markdown(post["content"])
            st.markdown(f"[前往完整文章]({post['url']})")

    with st.spinner("載入直播資料中..."):
        yt_title, yt_transcript = fetch_youtube_transcript()

    st.divider()
    st.subheader("✨ AI晨間簡報")

    today_posts = [p for p in mm_posts if p.get("date") == today_str]
    if today_posts:
        mm_source_posts = today_posts
        mm_source_label = today_str
    else:
        mm_source_posts = mm_posts[:1] if mm_posts else []
        mm_source_label = mm_posts[0].get("date", "最近一期") if mm_posts else "無資料"
        if mm_source_posts:
            st.caption(f"MM 今日無新短評，使用最近一期（{mm_source_label}）內容。")

    if not (yt_transcript and yt_transcript != "(無字幕)"):
        st.caption("游庭皓直播無字幕，簡報可能內容較少。")

    if st.button("生成今日簡報", type="primary"):
        if not groq_client and not _gemini_client:
            st.error("請在 .env 設定 GROQ_API_KEY 或 GEMINI_API_KEY")
        else:
            generated = {}
            if mm_source_posts:
                mm_ctx = "\n\n".join(f"{p['title']}\n{p['content']}" for p in mm_source_posts)
                with st.spinner("生成 MM 短評簡報..."):
                    mm_brief = ai_complete(f"""\
今天是 {today_str}，以下短評日期為 {mm_source_label}。

【MacroMicro 短評內容】
{mm_ctx}

請以研究員視角，用繁體中文以條列式生成市場觀點：""")
                generated["mm"] = {"text": mm_brief, "date": mm_source_label}
                save_briefing(today_str, "mm", {"text": mm_brief, "date": mm_source_label})

            with st.spinner("生成游庭皓直播簡報..."):
                yt_brief = ai_complete(f"""\
今天是 {today_str}。以下是游庭皓財經直播逐字稿（節錄）：
標題：{yt_title}
內容：
{yt_transcript[:2000]}

請用繁體中文生成研究員晨間重點整理，包含：
1. 今日市場開盤方向與重點
2. 台股關注方向（半導體、AI、低軌衛星等）
3. 值得追蹤的標的或事件

格式簡潔直接，像寫給自己的筆記。""")
            generated["yt"] = {"text": yt_brief, "title": yt_title, "date": today_str}
            save_briefing(today_str, "yt", {"text": yt_brief, "title": yt_title, "date": today_str})
            st.session_state["today_briefing"] = generated

    today_brief = st.session_state.get("today_briefing") or load_briefings().get(today_str, {})
    if today_brief:
        col_mm_brief, col_yt_brief = st.columns(2)
        with col_mm_brief:
            if "mm" in today_brief:
                mm_b = today_brief["mm"]
                mm_date = mm_b.get("date", today_str) if isinstance(mm_b, dict) else today_str
                mm_text = mm_b.get("text", mm_b) if isinstance(mm_b, dict) else mm_b
                st.markdown(f"#### 📰 MM 短評重點（{mm_date}）")
                st.markdown(mm_text)
        with col_yt_brief:
            if "yt" in today_brief:
                yt_b = today_brief["yt"]
                yt_date = yt_b.get("date", today_str) if isinstance(yt_b, dict) else today_str
                yt_text = yt_b.get("text", yt_b) if isinstance(yt_b, dict) else yt_b
                yt_ttl  = yt_b.get("title", yt_title) if isinstance(yt_b, dict) else yt_title
                st.markdown(f"#### 🎥 游庭皓直播重點（{yt_date}）")
                st.caption(yt_ttl)
                st.markdown(yt_text)

    st.divider()
    with st.expander("📅 過去一週簡報"):
        all_briefings = load_briefings()
        past_dates = [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, 8)
        ]
        available = [d for d in past_dates if d in all_briefings]
        if not available:
            st.write("尚無歷史簡報紀錄")
        else:
            sel_date = st.selectbox("選擇日期", available)
            past = all_briefings[sel_date]
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                if "mm" in past:
                    mm_b = past["mm"]
                    mm_date = mm_b.get("date", sel_date) if isinstance(mm_b, dict) else sel_date
                    mm_text = mm_b.get("text", mm_b) if isinstance(mm_b, dict) else mm_b
                    st.markdown(f"**📰 MM 短評（{mm_date}）**")
                    st.markdown(mm_text)
                else:
                    st.caption("該日無 MM 短評簡報")
            with col_p2:
                if "yt" in past:
                    yt_b = past["yt"]
                    yt_date = yt_b.get("date", sel_date) if isinstance(yt_b, dict) else sel_date
                    yt_text = yt_b.get("text", yt_b) if isinstance(yt_b, dict) else yt_b
                    yt_ttl  = yt_b.get("title", "") if isinstance(yt_b, dict) else ""
                    st.markdown(f"**🎥 游庭皓直播（{yt_date}）**")
                    if yt_ttl:
                        st.caption(yt_ttl)
                    st.markdown(yt_text)
                else:
                    st.caption("該日無直播簡報")


# ── 備忘錄 ────────────────────────────────────────────────
with tab_memo:
    st.subheader("投資備忘錄生成器")

    c1, c2 = st.columns([3, 1])
    ticker_raw = c1.text_input("輸入股票代號 / 公司名稱", placeholder="2330 / 台積電 / NVDA")
    fmt_select = c2.selectbox("格式", list(MEMO_PROMPTS.keys()))

    # 自動完成建議：打字即顯示，不需點開下拉
    ticker_input = ticker_raw
    if ticker_raw:
        tw_sugs = search_tw_stocks(ticker_raw)
        if tw_sugs:
            chosen = st.radio(
                "建議",
                [f"{c}　{n}" for c, n in tw_sugs[:8]],
                index=None,
                horizontal=True,
                label_visibility="collapsed",
            )
            if chosen:
                ticker_input = chosen.split("　")[0]

    if st.button("✨ AI 生成備忘錄", type="primary"):
        if not ticker_input:
            st.warning("請輸入股票代號或公司名稱")
        elif not groq_client and not _gemini_client:
            st.error("請在 .env 設定 GROQ_API_KEY 或 GEMINI_API_KEY")
        else:
            with st.spinner(f"解析 {ticker_input}..."):
                ticker = resolve_ticker(ticker_input)
            with st.spinner(f"分析 {ticker} 中..."):
                try:
                    info = get_stock_info(ticker)
                    memo = generate_memo(ticker, fmt_select, info)
                    st.session_state.update(memo=memo, ticker=ticker, fmt=fmt_select, info=info)
                except Exception as e:
                    st.error(f"錯誤：{e}")

    if "memo" in st.session_state:
        st.divider()
        st.markdown(st.session_state.memo)
        st.divider()

        if st.button("💾 存入 Notion"):
            if not NOTION_TOKEN:
                st.error("請設定 NOTION_TOKEN")
            else:
                with st.spinner("儲存中..."):
                    try:
                        push_to_notion(
                            st.session_state.ticker,
                            st.session_state.fmt,
                            st.session_state.memo,
                            st.session_state.info,
                        )
                        st.success("✅ 已存入 Notion！")
                    except Exception as e:
                        st.error(f"儲存失敗：{e}")


# ── 帳戶 ──────────────────────────────────────────────────
with tab_account:
    sj_api = get_sj_api()

    if not sj_api:
        st.warning("請在 .env 設定 SHIOAJI_API_KEY / SHIOAJI_SECRET_KEY")
        if "sj_error" in st.session_state:
            st.error(st.session_state["sj_error"])
    else:
        if st.button("🔄 重新整理帳戶資料", key="sj_refresh"):
            fetch_sj_stock_positions.clear()
            fetch_sj_futopt_positions.clear()
            fetch_sj_balance.clear()
            st.rerun()

        bal = fetch_sj_balance(sj_api)
        st.subheader("帳戶總覽")
        _bcols = st.columns(4)
        _bcols[0].metric("股票可用餘額",
                         f"${bal.get('stock_balance', 0):,.0f}" if "stock_balance" in bal else "—")
        _bcols[1].metric("期貨權益數",
                         f"${bal.get('equity', 0):,.0f}" if "equity" in bal else "—")
        _bcols[2].metric("可用保證金",
                         f"${bal.get('available_margin', 0):,.0f}" if "available_margin" in bal else "—")
        ri = bal.get("risk_indicator")
        _bcols[3].metric("風險指標", f"{ri:.1f}%" if ri is not None else "—")

        st.divider()

        df_cash, df_margin, df_short = fetch_sj_stock_positions(sj_api)

        st.subheader("現股持倉")
        if df_cash.empty:
            st.caption("無現股部位")
        else:
            st.caption(f"總損益：**{df_cash['損益(元)'].sum():+,.0f} 元**")
            st.dataframe(
                df_cash.style.applymap(
                    lambda v: "color:red" if isinstance(v, (int, float)) and v > 0
                    else ("color:green" if isinstance(v, (int, float)) and v < 0 else ""),
                    subset=["損益(元)", "損益%"],
                ),
                use_container_width=True, hide_index=True,
            )

        st.subheader("融資持倉")
        if df_margin.empty:
            st.caption("無融資部位")
        else:
            st.dataframe(df_margin, use_container_width=True, hide_index=True)

        st.subheader("融券持倉")
        if df_short.empty:
            st.caption("無融券部位")
        else:
            st.dataframe(df_short, use_container_width=True, hide_index=True)

        st.divider()

        st.subheader("期貨 / 選擇權持倉")
        df_fut = fetch_sj_futopt_positions(sj_api)
        if df_fut.empty:
            st.caption("無期貨部位")
        else:
            st.caption(f"總損益：**{df_fut['損益(元)'].sum():+,.0f} 元**")
            st.dataframe(df_fut, use_container_width=True, hide_index=True)


# ── 側邊欄 ────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 設定")
    st.write("Groq API",   "✅" if groq_client else "❌ Disconnected")
    st.write("Gemini API", "✅" if _gemini_client else "❌ Disconnected")
    st.write("Notion",     "✅" if NOTION_TOKEN else "❌ Disconnected")
    st.write("永豐帳戶",   "✅" if SJ_API_KEY else "❌ Disconnected")
    if SJ_API_KEY:
        st.caption("台股加權 / 台指期近：即時報價（永豐）\n其餘標的：15分鐘延遲（yfinance）")

    _providers = [p for p, ok in [("Groq", bool(groq_client)), ("Gemini", bool(_gemini_client))] if ok]
    if len(_providers) > 1:
        st.divider()
        st.radio("AI 模型", _providers, key="ai_provider", horizontal=True)
    elif _providers:
        st.session_state.setdefault("ai_provider", _providers[0])

    if not GROQ_KEY:
        st.divider()
        st.caption("**Groq API Key 取得步驟**")
        st.caption("1. 前往 console.groq.com")
        st.caption("2. 登入後 → API Keys → Create API Key")
        st.caption("3. 將 Key 貼入 .env 的 GROQ_API_KEY")
