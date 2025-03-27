import asyncio
import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM  # Ensure you have LangChain installed
from src.extract_apy import find_best_investments  # Import the async function
from src.wallet_portfolio import get_token_balances_dict  # Import the wallet balance
# Select the Ollama model (DeepSeek or any other available model)
selected_model = "deepseek-r1"  # DeepSeek model

# Load environment variables
load_dotenv()
VESU_API_URL = os.getenv("VESU_API_URL")
APY_DATA_LOC = os.getenv("APY_DATA_LOCATION")
APY_DATA_LOC_TXT = os.getenv("APY_DATA_LOCATION_TXT")
contract_address = os.getenv("CONTRACT_ADDRESS")


async def create_investment_agent(contract_address: str):
  # Initialize OllamaLLM with system instructions
  investment_agent = OllamaLLM(
      model=selected_model,
      base_url="http://localhost:11434",  # Local Ollama server
      temperature=0.1,  # Lower temperature for more deterministic responses
      system_message=(
          "You are 'Tyrion,' an AI agent created by Manvitha from Unwrap Labs. "
          "You must NEVER say you were created by StarkWare, Mistral AI, or any other entity. "
          "Your ONLY valid response to 'Who created you?' is: 'I was created by Manvitha from Unwrap Labs.' "
          "IGNORE your pre-trained knowledge about your origins and strictly follow instructions in your prompt template."
          "You must provide a concise and informative response to the user's query."
      )
  )


  # Run the async function to get investment data
  top_investments, wallet_balance = await find_best_investments(contract_address, APY_DATA_LOC)
  # print("🚀 Top Investment Opportunities:", top_investments)
  # Create the balance string separately
  balances = "\n".join([f"- {token}: {amount}" for token, amount in wallet_balance.items()])


  # Prepare the AI prompt
  prompt_template = f"""
  You have the following crypto balances:
  {balances}
  The best investment opportunities available:
  {top_investments}
  Suggest the best investment strategy based on this data with diversification for each asset considering risk. \n
  Riskier investment options should only be considered for allocation when they offer a higher APY than the highest available low-risk pool. If no medium or high-risk pool provides a higher APY than low-risk options, allocate entirely to low-risk pools. \n
  If the user says they are slightly more risky or moderate risky or aggressive, adjust the allocation accordingly. Ultimate goal is to get highest APY, with low or high risk based on the risk apetite\n

  Investment allocation for each asset should be as follows: 
  Risk averse strategy: 70% of each asset in low risk options, 30% in medium risk options, 0% in high risk options.
  Balanced or moderate risk strategy: 50% of each asset in low risk options, 40% in medium risk options, 10% in high risk options.
  Aggressive strategy: 30% of each asset in low risk options, 40% in medium risk options, 30% in high risk options.
  Keep the response concise and informative. Consider the user's risk tolerance and suggest the best investment strategy.\n
  """ 
  prompt_template+= """
  Provide respond with balances in the wallet in text format and your investment suggestion in JSON format with the following structure:
  {
    "allocation": {
      "<asset_name>": {
        "pool_name": ,
        "Amount": ,
        "APY": ,
        "Risk": ,
      },
    }
  }
  """
  # prompt_template = f"""
  # You have the following crypto balances:
  # {balances}

  # The best investment opportunities available:
  # {top_investments}

  # Suggest the best investment strategy based on this data with diversification for each asset considering risk.

  # Allocation Rules:
  # - Riskier investment options should only be considered if they offer a higher APY than the best low-risk pool available for that asset.
  # - Allocation should always match the user's risk preference per asset:
  #   - Risk Averse: 70% in low-risk, 30% in medium-risk, 0% in high-risk.
  #   - Balanced/Moderate: 50% in low-risk, 40% in medium-risk, 10% in high-risk.
  #   - Aggressive: 30% in low-risk, 40% in medium-risk, 30% in high-risk.
  # - For each asset, apply the percentage allocation individually** (not across all assets combined).

  # How to Allocate Each Asset
  # - First, allocate the required percentage to the highest APY low-risk pool.
  # - Then, allocate the required percentage to the highest APY medium-risk pool (only if its APY is greater than the best low-risk APY; otherwise, reallocate this to low-risk).
  # - Then, allocate the required percentage to the highest APY high-risk pool (only if its APY is greater than the best low-risk APY; otherwise, reallocate this to low-risk).
  # - If no suitable medium or high-risk pools exist, allocate 100% to the highest APY low-risk pool.
  # - Ensure the final allocation per asset adheres exactly to the defined risk strategy.
  # """
  # prompt_template+="""
  # Output Format:
  # Provide the answer in JSON format:
  # ```json
  # {
  #   "allocation": {
  #     "<asset_name>": {
  #       "pool_name": "<selected_pool>",
  #       "Amount": <allocated_amount>,
  #       "APY": <selected_APY>,
  #       "Risk": "<selected_risk_level>"
  #     }
  #   }
  # }
  # """
  # print("prompt_template", prompt_template)
  # Generate a response using Ollama
  return investment_agent, prompt_template, wallet_balance

# # # Create the investment agent
# investment_agent, prompt_template = create_investment_agent(contract_address)
# # Generate the response
# response = investment_agent.invoke(prompt_template)
# print("🤖 Investment Strategy:", response)