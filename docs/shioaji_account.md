# skills/shioaji_account.py

永豐金 Shioaji API 模組，提供即時行情快照與帳戶持倉查詢。

## 函式

### `get_sj_api()`
初始化並登入 Shioaji，`@st.cache_resource`（整個 session 只登入一次）。
需要 `.env` 設定 `SHIOAJI_API_KEY` / `SHIOAJI_SECRET_KEY`。
選擇性啟用憑證：`CA_PATH`, `CA_PASSWD`, `PERSON_ID`。

### `fetch_sj_tw_snapshot(_api) -> dict`
抓取台股加權（TSE001）與台指期近月即時快照。
回傳 `{"台股加權": (price, change_rate), "台指期近": (price, change_rate)}`，ttl=30s。

### `fetch_sj_stock_positions(_api) -> tuple[DataFrame, DataFrame, DataFrame]`
回傳 (現股, 融資, 融券) 三個 DataFrame，ttl=60s。

### `fetch_sj_futopt_positions(_api) -> DataFrame`
回傳期貨 / 選擇權持倉 DataFrame，ttl=60s。

### `fetch_sj_balance(_api) -> dict`
回傳帳戶餘額字典，包含 `stock_balance`, `equity`, `available_margin`, `risk_indicator`，ttl=60s。
