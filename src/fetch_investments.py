import os
import asyncio
from extract_apy import vesu_investment_options, strkfarm_investment_options, endur_investment_options  # Import the async function
import json

VESU_API_URL = os.getenv("VESU_API_URL")
STRKFARM_API_URL = os.getenv("STRKFARM_API_URL")
ENDUR_API_URL = os.getenv("ENDUR_API_URL")

APY_DATA_LOC_VESU = os.getenv("APY_DATA_LOCATION_VESU")
APY_DATA_LOC_STRKFARM = os.getenv("APY_DATA_LOCATION_STRKFARM")
APY_DATA_LOC_ENDUR = os.getenv("APY_DATA_LOCATION_ENDUR")
APY_DATA_LOC = os.getenv("APY_DATA_LOCATION")

async def fetch_and_save_data():
    """Fetches and saves investment data asynchronously"""
    
    # Fetch data asynchronously
    vesu_json = await vesu_investment_options(VESU_API_URL)
    strkfarm_json = strkfarm_investment_options(STRKFARM_API_URL)
    endur_json = endur_investment_options(ENDUR_API_URL)

    # Save data to files
    with open(APY_DATA_LOC_VESU, "w") as v_file:
        json.dump(vesu_json, v_file, indent=4)
    
    with open(APY_DATA_LOC_STRKFARM, "w") as s_file:
        json.dump(strkfarm_json, s_file, indent=4)

    with open(APY_DATA_LOC_ENDUR, "w") as e_file:
        json.dump(endur_json, e_file, indent=4)
    print(f"Data successfully saved to {APY_DATA_LOC_VESU}, {APY_DATA_LOC_STRKFARM}, {APY_DATA_LOC_ENDUR}")
    
    return vesu_json, strkfarm_json, endur_json

def load_json(filename):
    """Loads JSON data from a file if it exists"""
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return None

def combine_and_save(vesu_json, strkfarm_json, endur_json):
    """Combines the two investment data sets and saves the result"""
    combined_data = vesu_json + strkfarm_json + endur_json
    
    with open(APY_DATA_LOC, "w") as c_file:
        json.dump(combined_data, c_file, indent=4)
    
    print(f"Combined data saved to {APY_DATA_LOC}")

async def main():
    """Main function to run the script"""
    
    # Ask the user whether to load from files or fetch new data
    choice = input("Load existing data? (yes/no): ").strip().lower()
    
    if choice == "yes":
        vesu_json = load_json(APY_DATA_LOC_VESU) or []
        strkfarm_json = load_json(APY_DATA_LOC_STRKFARM) or []
        endur_json = load_json(APY_DATA_LOC_ENDUR) or []
    else:
        vesu_json, strkfarm_json, endur_json = await fetch_and_save_data()

    combine_and_save(vesu_json, strkfarm_json, endur_json)

if __name__ == "__main__":
    asyncio.run(main())
