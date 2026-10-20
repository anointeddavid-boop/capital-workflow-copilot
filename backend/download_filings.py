import os
import re
import sys

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
USER_AGENT = os.getenv("SEC_USER_AGENT")
if not USER_AGENT:
    sys.exit("SEC_USER_AGENT is missing from your .env file")
HEADERS = {"User-Agent": USER_AGENT}

COMPANY = "blackstone"
CIK = "0001393818"
OUT_DIR = "data/filings"


def latest_10k(cik):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    recent = r.json()["filings"]["recent"]
    for i, form in enumerate(recent["form"]):
        if form == "10-K":
            acc = recent["accessionNumber"][i].replace("-", "")
            doc = recent["primaryDocument"][i]
            date = recent["filingDate"][i]
            link = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{doc}"
            return link, date
    raise RuntimeError("No 10-K found")


def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "ix:header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def main():
    link, date = latest_10k(CIK)
    print("Filing date:", date)
    print("Downloading:", link)
    r = requests.get(link, headers=HEADERS, timeout=120)
    r.raise_for_status()
    print("Cleaning the text (this can take a minute)...")
    text = html_to_text(r.text)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{COMPANY}_10k_{date}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Saved:", path)
    print("Characters:", len(text))
    print("--- First 300 characters ---")
    print(text[:300])


if __name__ == "__main__":
    main()
