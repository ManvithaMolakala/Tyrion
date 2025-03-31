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
selected_model = "Mistral"

# Load environment variables
load_dotenv()
contract_address = os.getenv("CONTRACT_ADDRESS")

def get_investment_plan(contract_address: str, statement: str)->str:

    risk_profile_response = classify_risk(statement, model_name="deepseek-r1")

    
    # Create a regex pattern that matches any of the risk profile names (case-insensitive)
    pattern = r"\b(risk averse|balanced|aggressive)\b"
    
    match = re.search(pattern, risk_profile_response, re.IGNORECASE)
    
    if match:
        risk_profile = match.group(0).capitalize()  # Return the matched profile in proper case
    else:
        risk_profile = None  # No risk profile found
    
    print(risk_profile)
    user_assets = asyncio.run(get_token_balances_dict(contract_address))
    print(user_assets)
    investment_plan = allocate_assets(user_assets, risk_profile)  # Allocate funds
    investment_plan_json = json.dumps(investment_plan, indent=4)
    # Print the structured investment plan
    print(investment_plan_json)
    return investment_plan_json

user_statement = "Please analyse the funds in my wallet '0xabcd' and suggest an investment strategy. I do not want to take risk. Please look for a middle ground. Please suggest investment options."
invest_plan = get_investment_plan(contract_address, user_statement)