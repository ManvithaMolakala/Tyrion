import json
import asyncio
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from src.wallet_portfolio import get_token_balances_dict  
from src.investment_model import allocate_assets
from src.extract_filters import classify_risk

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Temporary in-memory storage for chat history (reset on refresh)
chat_history = {}
MAX_HISTORY = 3  # Stores 3 user messages max (no assistant messages stored)

# Helper functions for CORS
def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# Model name
selected_model = "deepseek-r1"

# Core function to generate investment plan
def get_investment_plan(messages: list) -> dict:
    # Use latest user message from the chat
    # Convert message history to a plain text format
    statement = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages])

    print(f"[DEBUG] Chat transcript:\n{statement}")

    # Extract Starknet contract address
    pattern = r"\b0x[a-fA-F0-9]{64}\b|\b\d{50,80}\b"
    contract_address = re.findall(pattern, statement)
    contract_address = str(contract_address[0]) if contract_address else None
    if not contract_address:
        raise ValueError("No valid contract address found in the statement.")

    print(f"[INFO] Using contract address: {contract_address}")



    filter_string = classify_risk(statement, model_name=selected_model)
    # Sanity check
    if not filter_string:
        raise ValueError("Received empty response from classify_risk()")

    # Strip markdown-like wrapping (e.g. ```json\n...\n```)
    raw_response = re.sub(r"```json|```", "", filter_string).strip()

    # try:
    #     filter_response = json.loads(filter_string)
    # except json.JSONDecodeError as e:
    #     print("Raw response before parsing:", repr(filter_string))
    #     raise e
    
    # Find the first JSON object using regex (this works if JSON is well-formed and at the start)
    match = re.search(r'\{[\s\S]*?\}', raw_response)
    if match:
        json_part = match.group(0)
        filter_response = json.loads(json_part)
        print(filter_response)
    else:
        print("No JSON found")

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

    print(f"[INFO] Risk profile classified as: {risk_profile}")

    # Get wallet assets
    user_assets = asyncio.run(get_token_balances_dict(contract_address))

    # Generate investment plan
    investment_plan = allocate_assets(user_assets, risk_profile, audited_only=is_audited, protocols=protocols, 
                    risk_levels=risk_levels, min_tvl=min_tvl, assets = assets)  # Allocate funds
    return investment_plan  # return dict instead of json string

# Health check route
@app.route('/status')
def index():
    return "Investment Plan API is running!"

# Main API endpoint
@app.route('/investment-plan', methods=['POST', 'OPTIONS'])
def investment_plan_api():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    data = request.json
    chat_id = data.get("chat_id")
    messages = data.get("messages", [])

    if not chat_id:
        return jsonify({"error": "Missing chat_id"}), 400
    if not messages:
        return jsonify({"error": "Missing messages"}), 400

    try:
        # Get user messages from the list
        user_messages = [m for m in messages if m["role"] == "user"]
        if not user_messages:
            return jsonify({"error": "No user message found"}), 400

        # Retrieve or initialize chat history
        history = chat_history.get(chat_id, [])

        # Add all new user messages to history
        history.extend(user_messages)

        # Trim to last MAX_HISTORY user messages
        history = history[-MAX_HISTORY:]

        # Save updated history
        chat_history[chat_id] = history

        print(f"[INFO] Updated chat history for {chat_id}: {history}")

        # Generate investment plan using updated history
        investment_plan = get_investment_plan(history)

        return _corsify_actual_response(jsonify({"investment_plan": investment_plan}))

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return _corsify_actual_response(jsonify({"error": str(e)})), 500

if __name__ == '__main__':
    app.run(debug=True)
