import os
import json
import asyncio
import re
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from src.wallet_portfolio import get_token_balances_dict  
from src.investment_model import allocate_assets
from src.extract_filters import classify_risk

# Load environment variables
load_dotenv()
contract_address = os.getenv("CONTRACT_ADDRESS")

app = Flask(__name__)

# Select the Ollama model
selected_model = "deepseek-r1"

def get_investment_plan(contract_address: str, statement: str) -> str:
    # Get risk profile
    risk_profile_response = classify_risk(statement, model_name=selected_model)

    # Regex to find risk profile
    pattern = r"\b(risk averse|balanced|aggressive)\b"
    match = re.search(pattern, risk_profile_response, re.IGNORECASE)
    
    risk_profile = match.group(0).capitalize() if match else None
    
    # Get user assets
    user_assets = asyncio.run(get_token_balances_dict(contract_address))
    
    # Allocate investment
    investment_plan = allocate_assets(user_assets, risk_profile)
    return json.dumps(investment_plan, indent=4)

@app.route('/investment-plan', methods=['POST'])
def investment_plan_api():
    data = request.json
    contract_address = data.get("contract_address")
    user_statement = data.get("statement")

    if not contract_address or not user_statement:
        return jsonify({"error": "Missing contract_address or statement"}), 400

    try:
        investment_plan = get_investment_plan(contract_address, user_statement)
        return jsonify({"investment_plan": json.loads(investment_plan)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
