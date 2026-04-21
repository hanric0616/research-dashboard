# skills/notion_push.py

將投資備忘錄存入 Notion 資料庫。

## 函式

### `push_to_notion(ticker, fmt, memo, info)`
建立一筆 Notion page，欄位對應：

| Notion 欄位 | 來源 |
|------------|------|
| 股票代號 | `ticker` |
| 公司名稱 | `info["shortName"]` |
| 備忘錄格式 | `fmt`（A/B/C） |
| 評等 | `info["recommendationKey"]` → Buy/Hold/Sell/觀察中 |
| 產業 | `classify_industry()` AI 分類 |
| 現價 / 目標價 | `info["currentPrice"]` / `info["targetMeanPrice"]` |

備忘錄正文以 2000 字為單位切片存入 paragraph blocks（Notion 單塊上限）。

## 依賴
- `NOTION_TOKEN` 和 `NOTION_DB_ID`（config.py）
- `skills/ai.classify_industry`
