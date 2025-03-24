import asyncio
import os
import httpx
from dotenv import load_dotenv
import requests
import re

# Load environment variables
load_dotenv()
api_url = os.getenv("API_URL")

# # Available tokens and their amounts
# wallet_balance = {
#     "USDC": 100,  # USDC balance
#     "ETH": 1,     # ETH balance
#     "STRK": 3000  # STRK balance
# }

async def fetch_investment_options(api_url):
    if not api_url:
        print("❌ API_URL is not set. Please check your environment variables.")
        return []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url)
            response.raise_for_status()
            data = response.json()

        # Validate API response
        if not isinstance(data, dict) or "data" not in data:
            print("❌ Invalid API response format.")
            return []

        investment_options = []

        for pool in data.get("data", []):
            for asset in pool.get("assets", []) or []:  # Ensure assets exist
                if asset is None:
                    continue

                stats = asset.get("stats", {}) or {}
                
                # Handle missing APY values
                supply_apy_raw = stats.get("supplyApy", {}).get("value", "0") or "0"
                supply_apy_decimals = stats.get("supplyApy", {}).get("decimals", 18) or 18

                defi_spring_apy_raw = stats.get("defiSpringSupplyApr", {}) or {}
                defi_spring_apy_value = defi_spring_apy_raw.get("value", "0") or "0"
                defi_spring_apy_decimals = defi_spring_apy_raw.get("decimals", 18) or 18

                try:
                    supply_apy = int(supply_apy_raw) / (10 ** supply_apy_decimals)
                    defi_spring_apy = int(defi_spring_apy_value) / (10 ** defi_spring_apy_decimals)
                except ValueError:
                    supply_apy, defi_spring_apy = 0, 0

                net_apy = supply_apy + defi_spring_apy  # Sum APYs

                # Handle Risk Rating Extraction
                risk_data = asset.get("risk") or {}
                risk_rating = "Unknown"  # Default value
                mdx_url = risk_data.get("mdxUrl")

                if mdx_url:
                    try:
                        mdx_response = requests.get(mdx_url)
                        mdx_response.raise_for_status()
                        mdx_content = mdx_response.text

                        # Extract risk rating from MDX content
                        match = re.search(r'export const rating = [\'"]([^\'"]+)[\'"]', mdx_content)
                        if match:
                            risk_rating = match.group(1)
                    except requests.RequestException as e:
                        print(f"⚠️ Failed to fetch MDX content: {e}")


                # Create investment option
                option = {
                    "name": asset.get("name", "Unknown"),
                    "asset": asset.get("symbol", "Unknown"),
                    "net_apy": net_apy,
                    "pool_name": asset.get("vToken", {}).get("name", "Unknown"),
                    "risk_rating": risk_rating,
                }
                investment_options.append(option)

        return investment_options

    except httpx.HTTPStatusError as e:
        print(f"❌ API Error: {e.response.status_code} - {e.response.text}")
    except httpx.TimeoutException:
        print("❌ Request timed out. Try increasing the timeout further.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return []

async def find_best_investments(wallet_balance):
    investments = await fetch_investment_options(api_url)

    if not investments:
        print("⚠️ No investment options fetched.")
        return "❌ No valid investment opportunities found."

    # Group investments by asset
    investment_by_asset = {}
    for inv in investments:
        if inv["asset"] in wallet_balance:
            investment_by_asset.setdefault(inv["asset"], []).append(inv)

    # Get top 3 strategies per asset
    top_strategies = []
    for asset, strategies in investment_by_asset.items():
        sorted_strategies = sorted(strategies, key=lambda x: x["net_apy"], reverse=True)[:3]

        # Total balance available for this asset
        total_balance = wallet_balance[asset]

        for strategy in sorted_strategies:
            strategy["investment_amount"] = total_balance / len(sorted_strategies) if sorted_strategies else 0
            strategy["allocation_percentage"] = (strategy["investment_amount"] / total_balance) * 100 if total_balance else 0

        top_strategies.extend(sorted_strategies)

    # Format output
    if not top_strategies:
        return "❌ No valid investment opportunities found."

    output = "\nTop Investment Options:\n"
    for i, strategy in enumerate(top_strategies, start=1):
        output += (
            f" The Pool,'{strategy['pool_name']}' with {strategy['net_apy']:.4%} APY for {strategy['name']} ({strategy['asset']})"
            f" and a {strategy['risk_rating']} risk rating\n"
        )

    return output

# # Run the script
# formatted_strategies = asyncio.run(find_best_investments(wallet_balance))
# print(formatted_strategies)
