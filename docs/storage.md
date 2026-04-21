# skills/storage.py

本機 JSON 資料存取，管理每日 AI 簡報紀錄。

## 函式

### `load_briefings() -> dict`
讀取 `data/briefings.json`，回傳 `{date: {mm: {...}, yt: {...}}}` 結構。

### `save_briefing(date_str, key, content)`
將單筆簡報寫入對應日期的 key（`"mm"` 或 `"yt"`），採 read-modify-write 模式。
