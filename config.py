import os
from dotenv import load_dotenv

load_dotenv()

GROQ_KEY      = os.getenv("GROQ_API_KEY")
GEMINI_KEY    = os.getenv("GEMINI_API_KEY")
NOTION_TOKEN  = os.getenv("NOTION_TOKEN")
NOTION_DB_ID  = "740be2f2d01e42488371225bf0dba6ce"

SJ_API_KEY    = os.getenv("SHIOAJI_API_KEY")
SJ_SECRET_KEY = os.getenv("SHIOAJI_SECRET_KEY")
SJ_CA_PATH    = os.getenv("CA_PATH")
SJ_CA_PASSWD  = os.getenv("CA_PASSWD")
SJ_PERSON_ID  = os.getenv("PERSON_ID")

GROQ_MODEL   = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.0-flash"

YT_CHANNEL     = "https://www.youtube.com/@yutinghaofinance/streams"
MM_QUICKIE_URL = "https://www.macromicro.me/quickie"

_BASE               = os.path.dirname(os.path.abspath(__file__))
BRIEFINGS_FILE      = os.path.join(_BASE, "data", "briefings.json")
CUSTOM_SYMBOLS_FILE = os.path.join(_BASE, "data", "custom_symbols.json")

INDUSTRIES = [
    "晶圓代工", "IC設計", "記憶體", "封測", "PCB", "IP", "ETF", "CPO/光通訊",
    "被動元件", "低軌衛星", "探針", "航運", "玻纖布", "軍工", "ABF載板", "生技",
    "金融業", "美股AI", "美股科技", "主動型ETF", "AI PC", "其他",
]

MEMO_PROMPTS = {
    "A 賣方報告式": """\
請撰寫賣方研究備忘錄，包含以下區塊（繁體中文）：

【評等】Buy / Hold / Sell　目標價：NT$/USD　現價：　上漲空間：
【核心論點】3個主要投資理由（條列，每點2句話以內）
【財務亮點】Markdown 表格：EPS實績、EPS預估共識、P/E、毛利率、評價（合理/偏高/偏低）
【三個風險】條列，每點說明潛在影響幅度
【催化劑】近期可能觸發上漲的具體事件或數據
【一句話結論】

數字要具體，格式清晰。""",

    "B 買方備忘錄式": """\
請撰寫買方基金備忘錄格式（繁體中文），使用以下 Markdown 結構輸出，每個區塊之間用 `---` 分隔：

---
## 倉位看法
> 持有 / 觀察加碼 / 減碼 / 不碰

---
## 為什麼持有
- （護城河或核心優勢，1句）
- （成長動能，1句）
- （估值或時機，1句）

---
## 進場條件
**股價區間：** NT$/USD　**或觸發事件：** 具體描述

---
## 離場條件
1. （觸發點一）
2. （觸發點二）
3. （觸發點三）

---
## 最大風險情境
描述最壞情況下的事件與潛在股價衝擊幅度（例：下跌 xx%）

像基金經理人的私人筆記，直接、不廢話。數字要具體。""",

    "C 一頁摘要": """\
請撰寫一頁快速摘要（繁體中文），60秒可讀完：

【為什麼現在】3個理由（條列，每點1句）
【三個風險】條列
【關鍵指標】Markdown 表格：EPS、P/E、目前評價
【結論】一句話：看多 / 看空 / 觀察 + 主要理由""",
}

DEFAULT_SYMBOLS = {
    "台股加權":  "^TWII",
    "台指期近":  "WTX&",
    "S&P 500":   "^GSPC",
    "NASDAQ":    "^IXIC",
    "費城半導體": "^SOX",
    "VIX":       "^VIX",
    "布蘭特原油": "BZ=F",
    "WTI":       "CL=F",
    "黃金":      "GC=F",
    "白銀":      "SI=F",
    "比特幣":    "BTC-USD",
    "USD/TWD":   "TWD=X",
}
