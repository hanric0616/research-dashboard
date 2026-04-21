# skills/market.py

市場行情模組，整合 yfinance（15 分鐘延遲）與 Shioaji 即時報價。

## 函式

### `fetch_indices(symbols: tuple) -> dict`
批次抓取多個 Yahoo Finance 標的的最新收盤價與漲跌幅。
回傳 `{name: (price, pct_change)}`，cache ttl=300s。

### `get_tw_futures_ticker() -> str | None`
自動偵測當月 SGX 台指期近月合約代號（格式：`TWN-{月份碼}{年份}.SI`）。

### `get_stock_info(ticker: str) -> dict`
抓取 yfinance `.info` 字典，cache ttl=600s。

### `resolve_ticker(query: str) -> str`
將公司名稱 / 中文名稱 / 數字代號轉換為 Yahoo Finance ticker。
優先順序：純數字 → 英文代號格式 → yfinance Search → AI 補足。

### `load_custom_symbols() -> dict`
讀取 `data/custom_symbols.json`，回傳 `{name: ticker}` 字典。

### `save_custom_symbols(syms: dict)`
覆寫 `data/custom_symbols.json`。
