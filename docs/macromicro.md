# skills/macromicro.py

MacroMicro 每日短評爬蟲，使用 Playwright 抓取 `macromicro.me/quickie`。

## 策略

1. **API 攔截（優先）**：監聽所有 response，攔截含 `quickie/collection/article` 且回傳 JSON 的 API 回應。
2. **DOM 解析（備援）**：透過 CSS selector（`article.quickie` 等）直接解析頁面 HTML。

頁面使用 `domcontentloaded` 而非 `networkidle`（後者在 SPA 頁面因 analytics 永遠不觸發）。

## 函式

### `fetch_mm_quickie() -> list[dict]`
主入口，cache ttl=3600s（1 小時）。
回傳 list of `{"date", "title", "content", "url"}`。

### `_parse_mm_articles(page) -> list[dict]`
內部函式，從 Playwright page 物件解析 DOM。
