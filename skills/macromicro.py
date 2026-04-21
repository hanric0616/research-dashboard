import platform
import re
import streamlit as st
from config import MM_QUICKIE_URL

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_IS_LINUX = platform.system() == "Linux"


# ── DOM 解析（共用）─────────────────────────────────────────

def _parse_selenium_articles(driver) -> list[dict]:
    from selenium.webdriver.common.by import By
    articles = []
    for selector in ["article.quickie.quickie-body", "article.quickie", ".quickie-body"]:
        articles = driver.find_elements(By.CSS_SELECTOR, selector)
        if articles:
            break
    results = []
    for article in articles[:7]:
        text = (article.get_attribute("textContent") or "").strip()
        text = re.sub(r"複製短評連結|看更多[^\n]*", "", text).strip()
        if len(text) < 30:
            continue
        url = MM_QUICKIE_URL
        try:
            links = article.find_elements(By.CSS_SELECTOR, "a[href*='/blog/']")
            if links:
                href = links[0].get_attribute("href") or ""
                url = href if href.startswith("http") else "https://www.macromicro.me" + href
        except Exception:
            pass
        m = re.match(r"^(\d{4}-\d{2}-\d{2})(【[^】]+】)(.*)$", text, re.DOTALL)
        if m:
            results.append({
                "date": m.group(1),
                "title": m.group(2),
                "content": m.group(3).strip()[:800],
                "url": url,
            })
        else:
            results.append({"date": "", "title": text[:60], "content": text[60:860], "url": url})
    return results


def _parse_playwright_articles(page) -> list[dict]:
    articles = []
    for selector in ["article.quickie.quickie-body", "article.quickie", ".quickie-body"]:
        articles = page.query_selector_all(selector)
        if articles:
            break
    results = []
    for article in articles[:7]:
        text = (article.text_content() or "").strip()
        text = re.sub(r"複製短評連結|看更多[^\n]*", "", text).strip()
        if len(text) < 30:
            continue
        url = MM_QUICKIE_URL
        blog_links = article.query_selector_all("a[href*='/blog/']")
        if blog_links:
            href = blog_links[0].get_attribute("href") or ""
            url = href if href.startswith("http") else "https://www.macromicro.me" + href
        m = re.match(r"^(\d{4}-\d{2}-\d{2})(【[^】]+】)(.*)$", text, re.DOTALL)
        if m:
            results.append({
                "date": m.group(1),
                "title": m.group(2),
                "content": m.group(3).strip()[:800],
                "url": url,
            })
        else:
            results.append({"date": "", "title": text[:60], "content": text[60:860], "url": url})
    return results


# ── Linux：selenium + 系統 chromium ─────────────────────────

def _fetch_mm_selenium() -> list[dict]:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument(f"--user-agent={_UA}")
    options.binary_location = "/usr/bin/chromium"

    driver = webdriver.Chrome(
        service=Service("/usr/bin/chromedriver"),
        options=options,
    )
    try:
        driver.get(MM_QUICKIE_URL)
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "article.quickie, article.quickie-body, .quickie-body")
                )
            )
        except Exception:
            import time
            time.sleep(15)
        results = _parse_selenium_articles(driver)
        return results or [{"date": "", "title": "無資料（MM 頁面無法解析）", "content": "", "url": MM_QUICKIE_URL}]
    except Exception as e:
        return [{"date": "", "title": f"無法取得 MM 短評（{e}）", "content": "", "url": MM_QUICKIE_URL}]
    finally:
        driver.quit()


# ── Mac：playwright ──────────────────────────────────────────

def _fetch_mm_playwright() -> list[dict]:
    from playwright.sync_api import sync_playwright

    api_articles: list[dict] = []

    def _on_response(resp):
        try:
            if resp.status != 200:
                return
            if not any(k in resp.url for k in ["quickie", "collection", "article"]):
                return
            if "json" not in resp.headers.get("content-type", ""):
                return
            data = resp.json()
            items = data if isinstance(data, list) else data.get("data", [])
            for item in items[:7]:
                title   = item.get("title") or item.get("name") or ""
                content = item.get("content") or item.get("body") or item.get("description") or ""
                date    = (item.get("publish_at") or item.get("created_at") or "")[:10]
                slug    = item.get("slug") or item.get("id") or ""
                url     = f"https://www.macromicro.me/blog/{slug}" if slug else MM_QUICKIE_URL
                if title or content:
                    api_articles.append({"date": date, "title": title,
                                         "content": str(content)[:800], "url": url})
        except Exception:
            pass

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--window-size=1280,900",
                    "--lang=zh-TW",
                ],
            )
            context = browser.new_context(user_agent=_UA, viewport={"width": 1280, "height": 900})
            page = context.new_page()
            page.on("response", _on_response)
            page.goto(MM_QUICKIE_URL, wait_until="commit", timeout=60000)
            try:
                page.wait_for_selector(
                    "article.quickie, article.quickie-body, .quickie-body",
                    timeout=30000,
                )
            except Exception:
                page.wait_for_timeout(15000)

            if api_articles:
                context.close()
                browser.close()
                return api_articles

            dom_results = _parse_playwright_articles(page)
            context.close()
            browser.close()
            return dom_results or [
                {"date": "", "title": "無資料（MM 頁面無法解析）", "content": "", "url": MM_QUICKIE_URL}
            ]
    except Exception as e:
        return [{"date": "", "title": f"無法取得 MM 短評（{e}）", "content": "", "url": MM_QUICKIE_URL}]


# ── 對外接口 ─────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_mm_quickie() -> list[dict]:
    if _IS_LINUX:
        return _fetch_mm_selenium()
    return _fetch_mm_playwright()
