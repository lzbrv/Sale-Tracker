# pip install playwright bs4 lxml
# python -m playwright install chromium  # or use your Chrome: channel="chrome"

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from bs4 import BeautifulSoup
import json, time, os, re

urlss = [
    'https://www.ssense.com/en-us/men/product/our-legacy/blue-extended-third-cut-jeans/14944791',
    'https://www.ssense.com/en-us/men/product/our-legacy/gray-third-cut-jeans/16231691',
    'https://www.ssense.com/en-us/men/product/our-legacy/blue-third-cut-jeans/16231841',
    'https://www.ssense.com/en-us/men/product/our-legacy/navy-third-cut-jeans/18101801'
]

PROFILE_DIR = os.path.abspath("./ssense_profile")  # will persist cookies here
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")


def _availability_str_to_bool(val: str):
    """
    Normalize assorted availability strings/URLs to True/False/None.
    True  => clearly in stock
    False => clearly not in stock or coming soon
    None  => unknown
    """
    if not val:
        return None
    v = val.strip().lower()
    # Common schema.org values (with/without http/https)
    if "instock" in v:
        return True
    if any(k in v for k in ["outofstock", "soldout", "preorder", "pre-order", "backorder", "back-order", "discontinued", "unavailable"]):
        return False
    return None


def _heuristic_in_stock(soup: BeautifulSoup):
    """
    Heuristic fallback from visible UI:
    - Buttons/links that say "Add to bag/cart" => in stock
    - "Sold out", "Out of stock", "Unavailable" => not in stock
    - Size pickers: any enabled/selectable size often implies stock
    """
    # 1) Obvious "sold out" / "out of stock" copy
    text = soup.get_text(" ", strip=True).lower()
    if re.search(r"\b(sold\s*out|out\s*of\s*stock|currently\s*unavailable|no\s*longer\s*available)\b", text):
        return False

    # 2) Buttons/CTAs
    btn_texts = []
    for el in soup.select("button, [role='button'], a, [data-test], [data-testid]"):
        t = el.get_text(" ", strip=True).lower()
        if t:
            btn_texts.append(t)
    joined = " | ".join(btn_texts)
    if re.search(r"\b(add\s*to\s*(bag|cart)|buy\s*now|checkout)\b", joined):
        return True
    if re.search(r"\b(sold\s*out|out\s*of\s*stock|notify\s*me|coming\s*soon|unavailable)\b", joined):
        return False

    # 3) Size/variant buttons (enabled vs disabled)
    # Many shops use disabled buttons or 'aria-disabled' on size options when OOS.
    # If we can find any enabled size option, assume in stock.
    enabled_size = soup.select(
        "button:not([disabled])[data-size], "
        "button:not([disabled])[data-test*='size'], "
        "button:not([disabled])[data-testid*='size'], "
        "li:not(.disabled) button, "
        "li:not(.is-disabled) button"
    )
    if enabled_size:
        return True

    # Unknown
    return None


def extract(html: str):
    soup = BeautifulSoup(html, "lxml")
    # Bail if Cloudflare/anti-bot
    if (soup.title and "just a moment" in soup.title.get_text(strip=True).lower()) or "__cf_chl_" in html.lower():
        return None

    name = price = currency = None
    in_stock = None  # we'll fill this

    # --- Primary: JSON-LD (schema.org/Product) ---
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except Exception:
            continue
        items = data.get("@graph", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = [items]
        for obj in items:
            if isinstance(obj, dict) and obj.get("@type") in ("Product", ["Product"]):
                # title
                name = name or obj.get("name")

                # price/currency + availability from offers
                offers = obj.get("offers")
                # offers may be dict or list
                if isinstance(offers, dict):
                    price = price or offers.get("price")
                    currency = currency or offers.get("priceCurrency")
                    in_stock = in_stock if in_stock is not None else _availability_str_to_bool(offers.get("availability"))
                elif isinstance(offers, list):
                    for off in offers:
                        if not isinstance(off, dict):
                            continue
                        price = price or off.get("price")
                        currency = currency or off.get("priceCurrency")
                        if in_stock is None:
                            maybe = _availability_str_to_bool(off.get("availability"))
                            if maybe is not None:
                                in_stock = maybe

    # --- Secondary: meta tags / microdata ---
    if in_stock is None:
        mt = soup.find("meta", attrs={"itemprop": "availability"}) or soup.find("link", attrs={"itemprop": "availability"})
        if mt:
            in_stock = _availability_str_to_bool(mt.get("content") or mt.get("href"))

    # --- Tertiary: page UI heuristics ---
    if in_stock is None:
        in_stock = _heuristic_in_stock(soup)

    # Title fallbacks
    if not name:
        mt = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if mt:
            name = mt.get("content")
    if not name:
        h = soup.select_one("h1, .product-title, [data-test='product-title']")
        if h:
            name = h.get_text(strip=True)

    # If nothing at all, return None; else include in_stock (default False if unknown)
    if not (name or price):
        return None

    return {
        "name": name,
        "price": price,
        "currency": currency,
        "in_stock": bool(in_stock) if in_stock is not None else False  # unknown => False per your requirement
    }


def scrape(url):
    with sync_playwright() as p:
        # 1st run: set headless=False to pass CF once; future runs can be headless=True
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,               # <-- persistent profile here
            channel="chrome",                        # use your installed Chrome (optional but helpful)
            headless=True,                           # set True after first successful run
            user_agent=UA,
            locale="en-US",
            timezone_id="America/New_York",
            color_scheme="dark",
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = context.new_page()
        context.set_default_timeout(15000)

        page.goto(url, wait_until="domcontentloaded", timeout=45000)

        # Wait for product selectors instead of "networkidle"
        try:
            page.wait_for_selector('script[type="application/ld+json"]', timeout=8000)
        except PWTimeout:
            try:
                page.wait_for_selector("h1, .product-title, [data-test='product-title']", timeout=8000)
            except PWTimeout:
                page.wait_for_timeout(4000)
                # optional one-time reload if still challenged
                if "moment" in (page.title() or "").lower():
                    page.reload(wait_until="domcontentloaded")
                    page.wait_for_timeout(4000)

        data = extract(page.content())

        time.sleep(1.0)
        context.close()
        return data


# Example:
#print(scrape(urlss[0]))
