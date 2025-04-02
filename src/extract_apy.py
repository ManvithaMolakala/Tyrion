import os
import httpx
from dotenv import load_dotenv
import requests
import re
import json

# Load environment variables
load_dotenv()
APY_DATA_LOC_VESU = os.getenv("APY_DATA_LOCATION_VESU")
APY_DATA_LOC_STRKFARM = os.getenv("APY_DATA_LOCATION_STRKFARM")
APY_DATA_LOC = os.getenv("APY_DATA_LOCATION")

# contract_address = os.getenv("CONTRACT_ADDRESS")


async def vesu_investment_options(api_url):
    if not api_url:
        print("❌ API_URL is not set. Please check your environment variables.")
        return []

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
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
                    "token_name": asset.get("name", "Unknown"),
                    "asset": asset.get("symbol", "Unknown").upper(),
                    "pool": asset.get("vToken", {}).get("name", "Unknown"),
                    "apy": net_apy*100,
                    "risk_rating": risk_rating,
                    "tvlusd": asset.get("currentUtilization", 0),
                    "is_audited": 1,
                    "protocol": "Vesu"
                }
                investment_options.append(option)
       # ✅ Save investment options in JSON format (structured)
        with open(APY_DATA_LOC_VESU, "w", encoding="utf-8") as file:
            json.dump(investment_options, file, indent=4)
        print("✅ Investment options JSON file saved successfully.")
        return investment_options

    except httpx.HTTPStatusError as e:
        print(f"❌ API Error: {e.response.status_code} - {e.response.text}")
    except httpx.TimeoutException:
        print("❌ Request timed out. Try increasing the timeout further.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return []


# Send a GET request to the API
def strkfarm_investment_options(api_url):
    response = requests.get(api_url)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        strategies = data.get("strategies", [])

        # Extract and structure the data
        extracted_data = []
        for strategy in strategies:
            pool = strategy.get("name", "N/A")
            apy = strategy.get("apy", 0) * 100  # Convert to percentage
            tvl = strategy.get("tvlUsd", 0)
            risk_factor = strategy.get("riskFactor", "N/A")
            is_audited = 1 if strategy.get("isAudited") else 0
            asset = strategy.get("contract", [{}])[0].get("name", "N/A") if strategy.get("contract") else "N/A"
            protocol = "Strkfarm"

            extracted_data.append({
                "asset": asset,
                "pool": pool,
                "apy": f"{apy:.2f}%",
                "risk_factor": risk_factor,
                "tvlusd": tvl,
                "is_audited": is_audited,
                "protocol": protocol
            })

        # Save the extracted data to a JSON file
        output_filename = APY_DATA_LOC_STRKFARM
        with open(output_filename, "w") as json_file:
            json.dump(extracted_data, json_file, indent=4)

        print(f"Data successfully saved to {output_filename}")

    else:
        print(f"Failed to fetch data: {response.status_code}")
    return extracted_data
    # return the extracted data


# Send a GET request to the API
def endur_investment_options(api_url):
    response = requests.get(api_url)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        strategies = data.get("strategies", [])

        # Extract and structure the data
        extracted_data = []
        for strategy in strategies:
            pool = strategy.get("name", "N/A")
            apy = strategy.get("apy", 0) * 100  # Convert to percentage
            tvl = strategy.get("tvlUsd", 0)
            risk_factor = strategy.get("riskFactor", "N/A")
            is_audited = 1 if strategy.get("isAudited") else 0
            asset = strategy.get("contract", [{}])[0].get("name", "N/A") if strategy.get("contract") else "N/A"
            protocol = "Strkfarm"

            extracted_data.append({
                "asset": asset,
                "pool": pool,
                "apy": f"{apy:.2f}%",
                "risk_factor": risk_factor,
                "tvlusd": tvl,
                "is_audited": is_audited,
                "protocol": protocol
            })

        # Save the extracted data to a JSON file
        output_filename = APY_DATA_LOC_STRKFARM
        with open(output_filename, "w") as json_file:
            json.dump(extracted_data, json_file, indent=4)

        print(f"Data successfully saved to {output_filename}")

    else:
        print(f"Failed to fetch data: {response.status_code}")
    return extracted_data
    # return the extracted data
