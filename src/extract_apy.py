import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_url = os.getenv("API_URL")

def fetch_investment_options(api_url):
    response = requests.get(api_url)
    data = response.json()
    
    investment_options = []
    for asset in data["data"][0]["assets"]:
        option = {
            "name": asset["name"],
            "asset": asset["symbol"],
            "apy": asset["stats"].get("supplyApy", {}).get("value", "N/A")
        }
        investment_options.append(option)
    
    return investment_options

investment_data = fetch_investment_options(api_url)
print(investment_data)