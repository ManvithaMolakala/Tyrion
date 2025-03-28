import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM  # Ensure you have LangChain installed
from wallet_portfolio import get_token_balances_dict  # Import the wallet balance
from investment_model import allocate_assets
import json
import asyncio


# Select the Ollama model (DeepSeek or any other available model)
selected_model = "Mistral"

# Load environment variables
load_dotenv()
APY_DATA_LOC = os.getenv("APY_DATA_LOCATION")
contract_address = os.getenv("CONTRACT_ADDRESS")


async def create_investment_agent(contract_address: str):
  # Initialize OllamaLLM with system instructions
  investment_agent = OllamaLLM(
      model=selected_model,
      base_url="http://localhost:11434",  # Local Ollama server
      temperature=0.1,  # Lower temperature for more deterministic responses
  )




# Load investment options from a JSON file
def load_investment_options(file_path):
    """Loads investment options from a JSON file."""
    with open(file_path, "r") as file:
        return json.load(file)


user_assets = asyncio.run(get_token_balances_dict(contract_address))
print(user_assets)


# Load data and allocate assets
investment_data = load_investment_options("src/data/investment_options.json")  # Load JSON file

investment_plan = allocate_assets(investment_data, user_assets, risk_profile="aggressive")  # Allocate funds

# Print the structured investment plan
print(json.dumps(investment_plan, indent=4))


