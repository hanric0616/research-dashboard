# skills/youtube.py

游庭皓 YouTube 直播逐字稿擷取，透過 `yt-dlp` CLI 工具下載。

## 函式

### `fetch_youtube_transcript() -> tuple[str, str]`
回傳 `(title, transcript)` 兩個字串，cache ttl=3600s。
- 抓取頻道最新一部影片（`--playlist-end 1`）
- 下載 `zh-TW` 自動字幕（VTT 格式）
- 去除時間碼、空行、重複行，截取前 3000 字元
- 無字幕時 transcript 回傳 `"(無字幕)"`，失敗時回傳錯誤訊息

## 依賴
需在系統安裝 `yt-dlp`：`brew install yt-dlp`
