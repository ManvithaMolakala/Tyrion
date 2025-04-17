import json
import time
import asyncio
import re
from datetime import datetime
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from src.wallet_portfolio import get_token_balances_dict  
from src.investment_model import allocate_assets
from src.extract_filters import classify_risk
from typing import Dict, List
from src.query_llm import classify_query
from src.chatbot_ollama import create_chatbot

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

chat_history = {}
MAX_HISTORY = 3
selected_model = "deepseek-r1"

LOG_FILE_PATH = "src/data/chat_logs.txt"
# Initialize the chatbot
RETRIEVER_PATH = "src/data/combined_retriever.pkl"


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def format_token_balances(token_balances: Dict[str, float]) -> List[Dict[str, float]]:
    return [
        {
            "symbol": symbol,
            "balance": balance,
            "usdValue": balance  # Placeholder
        }
        for symbol, balance in token_balances.items() if balance > 0
    ]

def get_contract_address(statement: str) -> str:
    pattern = r"\b0x[a-fA-F0-9]{64}\b|\b\d{50,80}\b"
    match = re.findall(pattern, statement)
    if not match:
        raise ValueError("Please provide a valid contract address.")
    print(f"[INFO] Using contract address: {match[0]}")
    return str(match[0])

def extract_query_category_and_response(prompt):
    try:
        # Try to extract the JSON structure from the prompt
        # Find the JSON part (after "Return the result in the following format:")
        start = prompt.find("{")
        end = prompt.rfind("}") + 1  # Include closing brace
        
        # Extract the JSON part
        json_part = prompt[start:end]
        
        # Parse the extracted JSON
        parsed_data = json.loads(json_part)
        
        # Extract query category and response
        query_category = parsed_data.get("category", "Unknown")
        response = parsed_data.get("response", "No response")
        
        return query_category, response
    
    except Exception as e:
        return f"Error: {str(e)}"
    
def get_investment_plan(statement: str) -> dict:
    classify_start = time.time()
    contract_address = get_contract_address(statement)
    classify_end = time.time()
    print(f"Time taken for classify_query: {classify_end - classify_start} seconds")
    
    investment_plan_start = time.time()
    user_assets = asyncio.run(get_token_balances_dict(contract_address))
    investment_plan_end = time.time()
    print(f"Time taken for get_token_balances_dict: {investment_plan_end - investment_plan_start} seconds")

    riskfilter_start = time.time()
    filter_string = classify_risk(statement, model_name=selected_model)
    riskfilter_end = time.time()
    print(f"Time taken for classify_risk: {riskfilter_end - riskfilter_start} seconds")

    if not filter_string:
        raise ValueError("Received empty response from classify_risk()")

    match = re.search(r'\{[\s\S]*?\}', filter_string)
    if not match:
        raise ValueError("No valid JSON filter response found")
    
    filter_response = json.loads(match.group(0))

    risk_profile = filter_response.get("risk_profile", "").capitalize()
    is_audited = filter_response.get("is_audited", False)
    protocols = filter_response.get("protocols", [])
    risk_levels = filter_response.get("risk_levels", [])
    min_tvl = filter_response.get("min_tvl", 0)
    assets = filter_response.get("assets", [])
    min_apy = filter_response.get("apy", [])

    pattern = r"\b(risk averse|balanced|aggressive)\b"
    match = re.search(pattern, risk_profile, re.IGNORECASE)
    
    if match:
        risk_profile = match.group(0).capitalize()
    else:
        risk_profile = None

    print(f"[INFO] Risk profile classified as: {risk_profile}")

    try:
        investment_plan, formatted_plan = allocate_assets(
            user_assets,
            risk_profile,
            audited_only=is_audited,
            protocols=protocols,
            risk_levels=risk_levels,
            min_tvl=min_tvl,
            assets=assets,
            min_apy=min_apy,
        )
        return formatted_plan
    except ValueError as ve:
        if "not enough values to unpack" in str(ve):
            raise ValueError("No investments found for the given filters.")
        else:
            raise ve

def log_chat_history(chat_id: str, messages: List[Dict[str, str]]):
    timestamp = datetime.utcnow().isoformat()
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n\n--- Chat ID: {chat_id} | Timestamp: {timestamp} UTC ---\n")
        for msg in messages:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            log_file.write(f"{role}: {content}\n")
        log_file.write(f"--- End of Chat ID: {chat_id} ---\n")

@app.route('/status')
def index():
    return "Investment Plan API is running!"

@app.route('/investment-plan', methods=['POST', 'OPTIONS'])
def investment_plan_api():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        chat_id = data.get("chat_id")
        messages = data.get("messages", [])

        if not chat_id or not messages:
            return jsonify({"error": "Missing chat_id or messages"}), 400

        user_messages = [m for m in messages if m["role"] == "user"]
        if not user_messages:
            return jsonify({"error": "No user message found"}), 400

        # Store limited history
        history = chat_history.get(chat_id, []) + user_messages
        history = history[-MAX_HISTORY:]
        chat_history[chat_id] = history

        # Log chat history
        log_chat_history(chat_id, history)

        # Format for classify_query
        previous_messages = history[:-1]
        current_message = history[-1]

        formatted_previous = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in previous_messages])
        formatted_current = f"{current_message['role'].capitalize()}: {current_message['content']}"

        statement = f"Previous chat:\n{formatted_previous}\n\nCurrent query:\n{formatted_current}"
        print(f"[DEBUG] ClassifyQuery input:\n{statement}")

        # Run query classifier
        classify_start = time.time()
        response = classify_query(statement)
        classify_end = time.time()
        print(f"Time taken for classify_query: {classify_end - classify_start} seconds")
        query_type,response_text = extract_query_category_and_response(response)
        print(f"[INFO] Query classified as: {query_type}")
        print(f"[INFO] Model response: {response_text}")

        if query_type == "balance_query":
            print(f"[INFO] Handling balance query")
            contract_address = get_contract_address(statement)
            user_assets = asyncio.run(get_token_balances_dict(contract_address))
            return _corsify_actual_response(jsonify({"balances": format_token_balances(user_assets)}))

        elif query_type == "investment_query":
            print(f"[INFO] Handling investment query")
            return _corsify_actual_response(jsonify({"investment_plan": get_investment_plan(statement)}))
        
        elif query_type == "other_query":
            # chatbot = create_chatbot(RETRIEVER_PATH, path_to_local_model)
            chatbot = create_chatbot(RETRIEVER_PATH)    
            chatbot_response = chatbot(statement)
            print(f"[INFO] Handling other query")
            return _corsify_actual_response(jsonify(chatbot_response["result"]))

        else:
            print(f"[WARN] Unrecognized query type: {query_type}")
            return _corsify_actual_response(jsonify({"error": "Sorry, I couldn't understand your query."}))

    except ValueError as ve:
        print(f"[ERROR] {str(ve)}")
        return _corsify_actual_response(jsonify({"error": str(ve)})), 400

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return _corsify_actual_response(jsonify({"error": "An unexpected error occurred."})), 500

if __name__ == '__main__':
    app.run(debug=True)
