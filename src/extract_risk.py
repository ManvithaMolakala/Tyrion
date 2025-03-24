import requests
import re

# Step 1: Fetch API data
api_url = "https://api.vesu.xyz/pools"
response = requests.get(api_url)
data = response.json()

# Step 2: Iterate through assets and fetch risk rating
for pool in data.get("data", []):  # Loop through pools
    for asset in pool.get("assets", []):  # Loop through assets in each pool
        asset_name = asset.get("name", "Unknown Asset")
        risk_data = asset.get("risk", {})
        mdx_url = risk_data.get("mdxUrl")

        if mdx_url:
            # Step 3: Fetch MDX file content
            mdx_response = requests.get(mdx_url)
            mdx_content = mdx_response.text

            # Step 4: Extract rating using regex
            match = re.search(r'export const rating = [\'"]([^\'"]+)[\'"]', mdx_content)

            if match:
                risk_rating = match.group(1)
                print(f"Risk Rating for {asset_name}: {risk_rating}")
            else:
                print(f"Rating not found in MDX file for {asset_name}.")
        else:
            print(f"MDX URL not found for {asset_name}.")
