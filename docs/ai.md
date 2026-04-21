# skills/ai.py

AI 生成模組，支援 Groq 和 Gemini 雙供應商，透過側邊欄 radio 切換。

## 匯出物件

| 名稱 | 類型 | 說明 |
|------|------|------|
| `groq_client` | `Groq \| None` | Groq SDK 實例，無 key 時為 None |
| `_gemini_client` | `Client \| None` | google-genai SDK 實例，無 key 時為 None |

## 函式

### `ai_complete(prompt) -> str`
統一入口，依 `st.session_state["ai_provider"]`（"Groq" / "Gemini"）路由。
若兩者皆無則拋出 `RuntimeError`。

### `groq_complete(prompt) -> str`
直接呼叫 Groq，model: `llama-3.3-70b-versatile`，temperature: 0.7。

### `gemini_complete(prompt) -> str`
直接呼叫 Gemini，model: `gemini-2.0-flash`。

### `generate_memo(ticker, fmt, info) -> str`
用 `ai_complete` 生成投資備忘錄，`fmt` 對應 `config.MEMO_PROMPTS` 的三種格式。

### `classify_industry(name, description) -> str`
從 `config.INDUSTRIES` 清單中選出最符合的產業，結果不在清單時退回 "其他"。
