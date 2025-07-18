from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bs4 import BeautifulSoup
import requests
import re

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def extract_emails(text):
    return list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))

def extract_phones(text):
    return list(set(re.findall(r"\b\d{10,13}\b", text)))

def extract_social_links(soup):
    social = {"facebook": "", "instagram": "", "twitter": ""}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "facebook.com" in href:
            social["facebook"] = href
        elif "instagram.com" in href:
            social["instagram"] = href
        elif "twitter.com" in href:
            social["twitter"] = href
    return social

def extract_faqs(soup):
    faqs = []
    tags = soup.find_all(["h2", "h3", "strong", "p"])
    for i, tag in enumerate(tags):
        q = tag.get_text(strip=True)
        if "?" in q:
            answer = ""
            for j in range(i + 1, min(i + 4, len(tags))):
                ans = tags[j].get_text(strip=True)
                if ans and "?" not in ans:
                    answer = ans
                    break
            faqs.append({"question": q, "answer": answer})
    return faqs[:10]

def get_full_product_catalog(base_url):
    try:
        url = base_url.rstrip("/") + "/products.json?limit=250"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            products = r.json().get("products", [])
            return [{
                "title": p.get("title"),
                "price": p.get("variants", [{}])[0].get("price"),
                "url": f"{base_url}/products/{p.get('handle')}"
            } for p in products]
    except:
        pass
    return []

@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "data": None})

@app.post("/extract_brand_data/", response_class=HTMLResponse)
async def extract(request: Request, website_url: str = Form(...)):
    try:
        r = requests.get(website_url, timeout=10)
        if r.status_code != 200:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid site", "data": None})

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        title = soup.title.string.strip() if soup.title else ""
        meta_desc = ""
        desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if desc and desc.get("content"):
            meta_desc = desc["content"]

        emails = extract_emails(text)
        phones = extract_phones(text)
        socials = extract_social_links(soup)
        faqs = extract_faqs(soup)

        links = {
            "About": "", "Contact": "", "Order Tracking": "",
            "Privacy Policy": "", "Return/Refund Policy": "", "Blogs": ""
        }
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True).lower()
            href = a["href"]
            if "about" in txt:
                links["About"] = href
            elif "contact" in txt:
                links["Contact"] = href
            elif "track" in txt:
                links["Order Tracking"] = href
            elif "privacy" in txt:
                links["Privacy Policy"] = href
            elif "return" in txt or "refund" in txt:
                links["Return/Refund Policy"] = href
            elif "blog" in txt:
                links["Blogs"] = href

        hero = []
        for a in soup.find_all("a", href=True):
            if "/products/" in a["href"]:
                txt = a.get_text(strip=True)
                if txt:
                    hero.append({"title": txt, "url": website_url.rstrip("/") + a["href"]})

        catalog = get_full_product_catalog(website_url)

        data = {
            "Title": title,
            "Meta Description": meta_desc,
            "Email(s)": emails,
            "Phone(s)": phones,
            "Hero Products Count": len(hero),
            "Hero Products": hero[:10],
            "Full Catalog Count": len(catalog),
            "Full Product Catalog": catalog[:20],
            "Social Handles": socials,
            "Important Links": links,
            "Brand FAQs": faqs
        }

        return templates.TemplateResponse("index.html", {"request": request, "data": data})

    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e), "data": None})
