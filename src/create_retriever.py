import requests
import asyncio
import aiohttp
import os
import random
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from chatbot_ollama import create_and_save_retriever  # Import chatbot retriever function
import json
# ────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────
BASE_URLS = {
    "starknet": "https://docs.starknet.io/",
    "strkfarm": "https://docs.strkfarm.com/",
    "nostra": "https://docs.nostra.finance/",
    "ekubo": "https://docs.ekubo.org/",
    "vesu": "https://docs.vesu.xyz/",
    "spiko": "https://docs.spiko.io/",
    "endur": "https://docs.endur.fi/docs/",
    "nimbora": "https://docs.nimbora.io/",
    "myswap": "https://docs.myswap.xyz/",
    "jediswap": "https://docs.jediswap.xyz/",
    "zklend": "https://docs.zklend.com/",


}

SCRAPE_MODES = {# 1 = Scrape, 0 = Load
    "starknet": 0,  
    "strkfarm": 0,
    "nostra": 0,
    "ekubo": 0,
    "vesu": 0,
    "spiko": 0,
    "endur": 0,
    "nimbora": 0,
    "myswap": 0,
    "jediswap": 0,
    "zklend": 0,

}

DEFI_LLAMA_API_URLS = {
    "protocols": "https://api.llama.fi/protocols",
    "yields": "https://api.llama.fi/pools",
}

DATA_DIR = "src/data"
API_DATA_DIR = os.path.join(DATA_DIR, "defillama")  
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(API_DATA_DIR, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
]

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ────────────────────────────────────────────────────────────────────
# Fetch and Save DeFiLlama API Data as Plain Text
# ────────────────────────────────────────────────────────────────────
def fetch_and_save_defillama_data():
    """Fetch data from DeFiLlama API and save it as text files."""
    all_data_files = []  # ✅ Now returning only file paths
    
    for name, url in DEFI_LLAMA_API_URLS.items():
        try:
            response = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                file_path = os.path.join(API_DATA_DIR, f"{name}.txt")

                # # Save JSON data directly to a file
                # with open(file_path, "w", encoding="utf-8") as f:
                #     json.dump(data, f, indent=4)  # Pretty-print JSON with indentation


                # Convert JSON data to a readable text format and save it
                with open(file_path, "w", encoding="utf-8") as f:
                    for entry in data:
                        if entry.get("chain", "").lower() == "starknet":  # Check if chain is Starknet (case-insensitive)
                            f.write(f" Protocol named {entry.get('name', 'N/A')}")
                            f.write(f" is on {entry.get('chain', 'N/A')} chain.")
                            f.write(f" The TVL of this protocol, {entry.get('name', 'N/A')} is ${round(entry.get('tvl', 0)):,.0f}.")
                            f.write(f" The hourly change in TVL for this protocol, {entry.get('name', 'N/A')} is ${round(entry.get('change_1h', 0) or 0):,.4f}.")
                            f.write(f" The daily change in TVL for this protocol, {entry.get('name', 'N/A')} is ${round(entry.get('change_1d', 0) or 0):,.4f}.")
                            f.write(f" The weekly change in TVL for this protocol, {entry.get('name', 'N/A')} is ${round(entry.get('change_7d', 0) or 0):,.4f}.")
                            f.write(f" It is a {entry.get('description', 'N/A')}")
                            f.write(f" The website url for this protocol can be found at '{entry.get('url', 'N/A')}'. ")
                            f.write(f" It belongs to {entry.get('category', 'N/A')} category")
                            f.write(f" The twitter profile of this protocol is '@{entry.get('twitter', 'N/A')}'. \n")
                            f.write("\n")
                            f.write("-" * 50 + "\n")
                            f.write("\n")

                logging.info(f"✅ Saved DeFiLlama data: {file_path}")
                all_data_files.append(file_path)  # ✅ Only store file paths

            else:
                logging.error(f"❌ Failed to fetch {name}, Status Code: {response.status_code}")

        except Exception as e:
            logging.warning(f"⚠️ Error fetching {name}: {e}")

    return all_data_files  # ✅ Returning file paths, not dictionaries

# ────────────────────────────────────────────────────────────────────
# Load Existing Data for Specific Websites
# ────────────────────────────────────────────────────────────────────
def load_existing_data(website_name):
    """Load saved data for a specific website."""
    file_path = os.path.join(DATA_DIR, f"{website_name}.txt")
    if os.path.exists(file_path):
        logging.info(f"📂 Loaded saved data for {website_name}")
        return [{"url": website_name, "content": ""}]  # Prevent text from being stored
    else:
        logging.warning(f"⚠️ No saved data found for {website_name}")
        return []

# ────────────────────────────────────────────────────────────────────
# Scrape or Load Data Based on SCRAPE_MODES
# ────────────────────────────────────────────────────────────────────
def save_combined_text_file(file_paths, combined_file_path):
    """Merge all scraped text files into a single file."""
    with open(combined_file_path, "w", encoding="utf-8") as outfile:
        for file_path in file_paths:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as infile:
                    outfile.write(f"====== {file_path} ======\n")  # Add separator
                    outfile.write(infile.read() + "\n\n")
            else:
                logging.warning(f"⚠️ Missing file: {file_path}")

    logging.info(f"✅ Combined text saved: {combined_file_path}")

def extract_internal_links(base_url):
    """Extract all internal links from a website."""
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        logging.error(f"❌ Failed to fetch {base_url}, Status Code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    links = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(base_url, href)  

        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.add(full_url)

    return list(links)

async def scrape_page(session, url, semaphore):
    """Scrape a single page asynchronously with rate limiting."""
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    async with semaphore:
        try:
            await asyncio.sleep(random.uniform(2, 5))  
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(f"❌ Failed to fetch {url}, Status Code: {response.status}")
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, "lxml")

                for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
                    tag.extract()

                text = soup.get_text(separator="\n")
                clean_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

                # 🛑 Filter out common unwanted text
                unwanted_phrases = ["Privacy Policy", "Terms of Service", "Cookies", "Subscribe", "Back to top"]
                clean_text = "\n".join(line for line in clean_text.split("\n") if not any(phrase in line for phrase in unwanted_phrases))

                return {"url": url, "content": clean_text}

        except Exception as e:
            print(f"⚠️ Error scraping {url}: {e}")
            return None

def save_scraped_data(website_name, scraped_data):
    """Save all scraped content for a website in a single text file."""
    file_path = os.path.join(DATA_DIR, f"{website_name}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in scraped_data:
            # f.write(f"====== {entry['url']} ======\n")  
            f.write(entry["content"] + "\n\n")

    print(f"✅ Saved combined data for {website_name}: {file_path}")


async def scrape_selected_websites():
    """Scrape or load websites, then combine into a single file."""
    all_data_files = []

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(3)

        for website_name, base_url in BASE_URLS.items():
            mode = SCRAPE_MODES.get(website_name, 0)

            if mode == 1:
                logging.info(f"🔄 Scraping {website_name} ({base_url})...")
                internal_links = extract_internal_links(base_url)
                tasks = [scrape_page(session, link, semaphore) for link in internal_links]
                results = await asyncio.gather(*tasks)

                scraped_data = [res for res in results if res]
                save_scraped_data(website_name, scraped_data)
            else:
                logging.info(f"📂 Loading saved data for {website_name}...")

            file_path = os.path.join(DATA_DIR, f"{website_name}.txt")
            all_data_files.append(file_path)

    # 🔥 Fetch and append DeFiLlama data (file paths)
    api_data = fetch_and_save_defillama_data()
    all_data_files.extend(api_data)

    # 🔥 Save combined file
    combined_file_path = os.path.join(DATA_DIR, "combined.txt")
    save_path = os.path.join(DATA_DIR, "combined_retriever.pkl")
    save_combined_text_file(all_data_files, combined_file_path)

    # 🔥 Pass the combined file to retriever
    create_and_save_retriever(combined_file_path, save_path)

    logging.info("✅ Retriever updated!")

asyncio.run(scrape_selected_websites())
