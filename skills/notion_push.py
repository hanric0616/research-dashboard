from notion_client import Client as NotionClient
from config import NOTION_TOKEN, NOTION_DB_ID
from skills.ai import classify_industry


def push_to_notion(ticker: str, fmt: str, memo: str, info: dict):
    notion = NotionClient(auth=NOTION_TOKEN)

    industry = classify_industry(
        info.get("shortName", ticker),
        info.get("longBusinessSummary", ""),
    )

    rec = info.get("recommendationKey", "").lower()
    rating = {
        "buy": "Buy", "strong_buy": "Buy",
        "hold": "Hold",
        "sell": "Sell", "underperform": "Sell",
    }.get(rec, "觀察中")

    price  = info.get("currentPrice") or info.get("regularMarketPrice")
    target = info.get("targetMeanPrice")

    props = {
        "股票代號": {"title": [{"text": {"content": ticker}}]},
        "公司名稱": {"rich_text": [{"text": {"content": info.get("shortName", ticker)}}]},
        "備忘錄格式": {"select": {"name": fmt}},
        "評等":       {"select": {"name": rating}},
        "產業":       {"select": {"name": industry}},
    }
    if price:  props["現價"]  = {"number": float(price)}
    if target: props["目標價"] = {"number": float(target)}

    chunks = [memo[i:i + 2000] for i in range(0, len(memo), 2000)]
    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": c}}]},
        }
        for c in chunks
    ]

    notion.pages.create(
        parent={"database_id": NOTION_DB_ID},
        properties=props,
        children=children,
    )
