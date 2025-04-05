import json
import asyncio
import re
from flask import Flask, request, jsonify, make_response
from src.wallet_portfolio import get_token_balances_dict  
from src.investment_model import allocate_assets
from src.extract_filters import classify_risk
from flask_cors import CORS

app = Flask(__name__)
# CORS(app) 
# CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# Select the Ollama model
selected_model = "deepseek-r1"

def get_investment_plan(statement: str) -> str:

    # Extract Starknet contract addresses (66-character hex or large decimal numbers)
    pattern = r"\b0x[a-fA-F0-9]{64}\b|\b\d{50,80}\b"
    contract_address = re.findall(pattern, statement) 
    print(f"Contract Address: {contract_address}")
    contract_address = str(contract_address[0]) if contract_address else None
    if not contract_address:
        raise ValueError("No valid contract address found in the statement.")
    print(f"Contract Address: {contract_address}")

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

@app.route('/status')
def index():
    return "Investment Plan API is running!"

@app.route('/investment-plan', methods=['POST', 'OPTIONS'])
def investment_plan_api():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()

    data = request.json
    print(data)
    user_statement = data.get("statement")

    if not user_statement:
        return jsonify({"error": "Missing statement"}), 400

    try:
        investment_plan = get_investment_plan(user_statement)
        return _corsify_actual_response(jsonify({"investment_plan": json.loads(investment_plan)}))
    except Exception as e:
        return _corsify_actual_response(jsonify({"error": str(e)})), 500

if __name__ == '__main__':
    app.run(debug=True)
