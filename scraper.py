import requests
from bs4 import BeautifulSoup
import re

def extract_insights(url):
    result = {"source": url}
    try:
        # Product Catalog
        try:
            products = requests.get(f"{url}/products.json", timeout=10).json()
            result["product_catalog"] = products.get("products", [])
        except:
            result["product_catalog"] = []

        # Get homepage content
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        # Hero Products
        hero = soup.find_all("a", href=re.compile("/products/"))
        result["hero_products"] = list(set([url + link['href'] for link in hero if '/products/' in link['href']]))

        # Emails & Phones
        text = soup.get_text()
        result["emails"] = re.findall(r"\S+@\S+", text)
        result["phones"] = re.findall(r"\+?\d[\d\s-]{8,15}\d", text)

        # Social Media
        result["socials"] = {
            "instagram": re.findall(r"instagram\.com/[^\s\"']+", html),
            "facebook": re.findall(r"facebook\.com/[^\s\"']+", html),
        }

        # About, Policies, FAQs (try fixed URLs)
        def try_page(slug):
            try:
                res = requests.get(f"{url}/{slug}", timeout=10)
                if res.status_code == 200:
                    return BeautifulSoup(res.text, "html.parser").get_text(strip=True)
            except:
                return None

        result["about"] = try_page("pages/about") or try_page("about")
        result["privacy_policy"] = try_page("policies/privacy-policy")
        result["refund_policy"] = try_page("policies/refund-policy")
        result["faqs"] = try_page("pages/faqs") or try_page("faqs")

        # Important Links
        result["important_links"] = re.findall(r'href="([^"]+)"', html)

        return result

    except Exception as e:
        print("SCRAPER ERROR:", e)
        return None
