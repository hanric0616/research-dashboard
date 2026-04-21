import pandas as pd
import streamlit as st
from config import SJ_API_KEY, SJ_SECRET_KEY, SJ_CA_PATH, SJ_CA_PASSWD, SJ_PERSON_ID


@st.cache_resource
def get_sj_api():
    if not all([SJ_API_KEY, SJ_SECRET_KEY]):
        return None
    try:
        import shioaji as sj
        api = sj.Shioaji()
        api.login(api_key=SJ_API_KEY, secret_key=SJ_SECRET_KEY)
        if all([SJ_CA_PATH, SJ_CA_PASSWD, SJ_PERSON_ID]):
            api.activate_ca(ca_path=SJ_CA_PATH, ca_passwd=SJ_CA_PASSWD, person_id=SJ_PERSON_ID)
        return api
    except Exception as e:
        st.session_state["sj_error"] = str(e)
        return None


def _sj_stock_name(api, code: str) -> str:
    try:
        return api.Contracts.Stocks[code].name
    except Exception:
        return code


def _sj_direction(pos) -> str:
    return "多" if "Buy" in str(pos.direction) else "空"


@st.cache_data(ttl=30)
def fetch_sj_tw_snapshot(_api) -> dict:
    result = {}
    try:
        snaps = _api.snapshots([_api.Contracts.Indexs.TSE.TSE001])
        if snaps:
            s = snaps[0]
            result["台股加權"] = (float(s.close), float(s.change_rate))
    except Exception:
        pass
    try:
        txf_list = list(_api.Contracts.Futures.TXF)
        near = sorted(txf_list, key=lambda c: c.delivery_date)[0]
        snaps = _api.snapshots([near])
        if snaps:
            s = snaps[0]
            result["台指期近"] = (float(s.close), float(s.change_rate))
    except Exception:
        pass
    return result


@st.cache_data(ttl=60)
def fetch_sj_stock_positions(_api) -> tuple:
    cash, margin, short = [], [], []
    try:
        for pos in _api.list_positions(_api.stock_account):
            qty = pos.quantity / 1000
            pct = round((pos.last_price - pos.price) / pos.price * 100, 2) if pos.price else 0
            row = {
                "代號": pos.code,
                "名稱": _sj_stock_name(_api, pos.code),
                "方向": _sj_direction(pos),
                "部位(張)": round(qty, 1),
                "成本均價": pos.price,
                "現價": pos.last_price,
                "損益(元)": round(pos.pnl),
                "損益%": pct,
            }
            cond = str(pos.cond)
            if "MarginBuying" in cond:
                row["融資金額"] = pos.margin_purchase_amount
                margin.append(row)
            elif "ShortSelling" in cond:
                row["融券保證金"] = pos.short_sale_margin
                short.append(row)
            else:
                cash.append(row)
    except Exception:
        pass
    return pd.DataFrame(cash), pd.DataFrame(margin), pd.DataFrame(short)


@st.cache_data(ttl=60)
def fetch_sj_futopt_positions(_api) -> pd.DataFrame:
    rows = []
    try:
        for pos in _api.list_positions(_api.futopt_account):
            rows.append({
                "商品代號": pos.code,
                "方向": _sj_direction(pos),
                "部位(口)": pos.quantity,
                "成本均價": pos.price,
                "現價": pos.last_price,
                "損益(元)": round(pos.pnl),
            })
    except Exception:
        pass
    return pd.DataFrame(rows)


@st.cache_data(ttl=60)
def fetch_sj_balance(_api) -> dict:
    out = {}
    try:
        bal = _api.account_balance()
        out["stock_balance"] = bal.acc_balance
    except Exception:
        pass
    try:
        mg = _api.margin(_api.futopt_account)
        out["equity"]             = mg.equity
        out["available_margin"]   = mg.available_margin
        out["risk_indicator"]     = mg.risk_indicator
        out["maintenance_margin"] = mg.maintenance_margin
    except Exception:
        pass
    return out
