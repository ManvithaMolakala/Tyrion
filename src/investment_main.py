import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM  # Ensure you have LangChain installed
from wallet_portfolio import get_token_balances_dict  # Import the wallet balance
from investment_model import allocate_assets
from extract_filters import classify_risk
import json
import asyncio
import re


# Select the Ollama model (DeepSeek or any other available model)
selected_model = "deepseek-r1"

# Load environment variables
load_dotenv()
contract_address = os.getenv("CONTRACT_ADDRESS")

def get_investment_plan(statement: str)->str:

    # Extract Starknet contract addresses (66-character hex or large decimal numbers)
    pattern = r"\b0x[a-fA-F0-9]{64}\b|\b\d{50,80}\b"
    contract_address = re.findall(pattern, statement) 
    contract_address = str(contract_address[0]) if contract_address else None
    if not contract_address:
        raise ValueError("No valid contract address found in the statement.")
    print(f"Contract Address: {contract_address}")

    filter_string = classify_risk(statement, model_name=selected_model)
    # Sanity check
    if not filter_string:
        raise ValueError("Received empty response from classify_risk()")

    # Strip markdown-like wrapping (e.g. ```json\n...\n```)
    filter_string = re.sub(r"```json|```", "", filter_string).strip()

    try:
        filter_response = json.loads(filter_string)
    except json.JSONDecodeError as e:
        print("Raw response before parsing:", repr(filter_string))
        raise e

    risk_profile = filter_response["risk_profile"]
    is_audited = filter_response["is_audited"]
    protocols = filter_response["protocols"]
    risk_levels = filter_response["risk_levels"]
    min_tvl = filter_response["min_tvl"]
    assets = filter_response["assets"]
    # Create a regex pattern that matches any of the risk profile names (case-insensitive)
    pattern = r"\b(risk averse|balanced|aggressive)\b"
    match = re.search(pattern, risk_profile, re.IGNORECASE)
    
    if match:
        risk_profile = match.group(0).capitalize()  # Return the matched profile in proper case
    else:
        risk_profile = None  # No risk profile found
    
    print(risk_profile)
    user_assets = asyncio.run(get_token_balances_dict(contract_address))
    print("Balances",user_assets)
    investment_plan = allocate_assets(user_assets, risk_profile, audited_only=is_audited, protocols=protocols, 
                    risk_levels=risk_levels, min_tvl=min_tvl, assets = assets)  # Allocate funds
    investment_plan_json = json.dumps(investment_plan, indent=4)
    # Print the structured investment plan
    print(investment_plan_json)
    return investment_plan_json

# user_statement = f"Please analyse the funds in my wallet {contract_address} and suggest an investment strategy. I do not want to take risk. Please look for a middle ground. Please suggest investment options."
user_statement = "{'role': 'user', 'content': 'update risk to balanced'}, {'role': 'user', 'content': '0x04cced5156ab726bf0e0ca2afeb1f521de0362e748b8bdf07857b088dbc7b457 aggresive risk'}, {'role': 'user', 'content': 'update risk to balanced'}]"
invest_plan = get_investment_plan(user_statement)