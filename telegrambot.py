from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from src.chatbot_ollama import create_chatbot
from src.wallet_portfolio import get_token_balances_dict
from src.extract_filters import classify_risk, output_bot
from src.investment_model import allocate_assets
import json
import logging
import os
import sqlite3
import re
import asyncio

# ✅ Fix event loop issue
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Load bot token securely
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("Missing TELEGRAM_BOT_TOKEN. Set it as an environment variable.")
    exit(1)

BOT_USERNAME = os.getenv("BOT_USERNAME")


# Initialize the chatbot
RETRIEVER_PATH = "src/data/combined_retriever.pkl"
# chatbot = create_chatbot(RETRIEVER_PATH, path_to_local_model)
chatbot = create_chatbot(RETRIEVER_PATH)

logger.info("Chatbot initialized")

# Initialize SQLite database
DB_PATH = os.getenv("CHAT_HISTORY_PATH")  # Path to the SQLite database

def init_db():
    """Creates the database if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            username TEXT,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_message(chat_id, username, role, message):
    """Saves messages to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messages (chat_id, username, role, message)
        VALUES (?, ?, ?, ?)
    """, (chat_id, username, role, message))
    conn.commit()
    conn.close()

def get_last_messages(chat_id, limit=2):
    """Retrieves the last 'limit' messages from chat history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, message FROM messages 
        WHERE chat_id = ? AND role = 'user'
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (chat_id, limit))
    
    rows = cursor.fetchall()
    conn.close()

    history = "\n".join([f"{row[0].capitalize()}: {row[1]}" for row in reversed(rows)])
    return history if history else ""

init_db()  # Ensure the database is set up

MAX_MESSAGE_LENGTH = 4000

def split_message(message, max_length=MAX_MESSAGE_LENGTH):
    """Splits long messages into chunks that fit within Telegram's limits."""
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm TyrionAI. How can I assist you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "I am Tyrion, a chatbot created by Manvitha from Unwrap labs. I can help you with any questions about Starknet. Just ask me anything!"
    await update.message.reply_text(help_text)

async def starknet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Starknet is a Layer 2 scaling solution for Ethereum, designed to enhance scalability and reduce transaction costs while maintaining security.")

async def staking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Staking involves locking up cryptocurrency to support a blockchain network and earn rewards in return.")

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cryptocurrency is a digital or virtual currency that uses cryptography for security and operates on decentralized networks based on blockchain technology.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles wallet-related queries while considering previous conversation context."""
    text = update.message.text.strip().lower()
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = user.username or user.first_name or user.last_name or f"User_{user.id}"

    # Retrieve previous messages for context
    previous_query = get_last_messages(chat_id, limit=1)
    print(f"Previous queries: {previous_query}")  # Debugging output

    save_message(chat_id, username, "user", text)
    finalprompt = f"""previous query: {previous_query} \n current_statement{text}"""

    # wallet_keywords = {"wallet", "balance", "portfolio", "funds", "invest", "investment", "strategy"}
    # Extract Starknet contract addresses (66-character hex or large decimal numbers)
    pattern = r"\b0x[a-fA-F0-9]{64}\b|\b\d{50,80}\b"
    contract_addresses = re.findall(pattern, finalprompt)
    print(finalprompt)
    if not contract_addresses:
        await update.message.reply_text("⚠️ No valid Starknet address found in your message.")
        return
    
    async def get_investment_plan(contract_address: str, statement: str)->str:
        risk_profile_response = classify_risk(statement, model_name="deepseek-r1")
        # Create a regex pattern that matches any of the risk profile names (case-insensitive)
        pattern = r"\b(risk averse|balanced|aggressive|none)\b"
        
        match = re.search(pattern, risk_profile_response, re.IGNORECASE)
        
        if match:
            risk_profile = match.group(0).capitalize()  # Return the matched profile in proper case
            risk_profile_user = risk_profile
        else:
            risk_profile = None  # No risk profile found

        user_assets = await(get_token_balances_dict(contract_address))
        if risk_profile == "None":
            risk_profile = "balanced"
            risk_profile_user = "Balanced. Since you have not mentioned your risk apetite, investment suggestion is provided to maintain a balanced portfolio."

        investment_plan = allocate_assets(user_assets, risk_profile)  # Allocate fundss
        investment_plan_json = json.dumps(investment_plan, indent=4)
        investment_plan_text = "Investment Strategy Overview:\n\n"
    
        for asset, allocations in investment_plan.items():
            investment_plan_text += f"{asset} Allocation:\n"
            for allocation in allocations:
                investment_plan_text += (
                    f"- Pool: {allocation['pool']}\n"
                    f"- Allocated Amount: {allocation['allocated_amount']}\n"
                    f"- Percentage Allocation: {allocation['% allocation']}%\n"
                    f"- Net APY: {allocation['net_apy']}%\n"
                    f"- Risk Level: {allocation['risk'].capitalize()}\n\n"
                )
    
        # Print the structured investment plan
        return investment_plan_text, user_assets, risk_profile_user
    contract_address = contract_addresses[0]  # Use the first valid address
    invest_plan, user_assets, risk_profile_user = await get_investment_plan(contract_address, finalprompt)
    # Construct chatbot prompt with previous messages
    # full_prompt = (
    #     # f"I am sharing our previous conversation here:\n\n"
    #     # f"Previous conversation:\n{previous_conversation}\n\n"
    #     # f"Use this only if the user is referring to past messages. Otherwise, answer only the current query.\n"
    #     f"User's request: {text}\n\n"
    #     # f"Wallet Address: {contract_address}\n\n"
    #     # f"In case the user asks about the wallet balance, here is the wallet balance: {wallet_balance}\n\n"
    #     f"In case the user is asking about investment options: use the following {prompt_template}. Else just respond with  \n\n"
    #     f"Bot:"
    # )

    # ✅ Show "typing..." in the background without blocking execution
    asyncio.create_task(context.bot.send_chat_action(chat_id=chat_id, action="typing"))
    logger.info(f"[Wallet Query] {username}: {update.message.text}")

    # # Generate the response
    # response = investment_agent.invoke(full_prompt)
    # # response = entire_response["result"].split("point):", 1)[-1].strip()
    response = f"Your assets: {user_assets}\n \nYour risk profile: {risk_profile_user} \n \n {invest_plan}"
    # Save and send response
    save_message(chat_id, "TyrionAI", "bot", response)
    await update.message.reply_text(response)
    logger.info(f"[Bot] TyrionAI: {response}")


# # Function to handle user messages
# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not update.message or not update.message.text:
#         logger.warning("Received an update without a text message.")
#         return
    
#     text = update.message.text
#     chat_id = update.message.chat.id
#     user = update.message.from_user
#     username = user.username or user.first_name or user.last_name or f"User_{user.id}"

#     # ✅ Show "typing..." in the background without blocking execution
#     asyncio.create_task(context.bot.send_chat_action(chat_id=chat_id, action="typing"))
#     logger.info(f"[User] {username}: {text}")
    

#     previous_conversation = get_last_messages(chat_id, limit=2)
#     save_message(chat_id, username, "user", text)

#     full_prompt = f"I am sharing our previous conversation here: \n\n Previous conversation: \n{previous_conversation}. \n\n Use the previous conversation to answer my question only if the user is asking a follow-up question or is referring to the previous question. Else ignore the previous conversation and answer only the current question. \n Here is the New question: {text}. \n Bot:"
#     # full_prompt = text
#     print("full prompt:", full_prompt)
#     try:
#         entire_response = chatbot.invoke({"query": full_prompt})
#         # entire_response = chatbot.process_query({"query": full_prompt})
#         response = entire_response["result"].split("point):", 1)[-1].strip()
#         retrieved_docs = entire_response.get("source_documents", [])  # List of retrieved documents
#         # ✅ Print retrieved docs
#         if retrieved_docs:
#             print("\n========== RETRIEVED CONTEXT ==========")
#             for idx, doc in enumerate(retrieved_docs, start=1):
#                 print(f"🔹 Document {idx}: {doc.page_content[:500]}")  # Print first 500 chars
#             print("=================================")
#         else:
#             print("\n⚠️ No relevant documents retrieved!\n")    
#     except Exception as e:
#         logger.error(f"Chatbot error: {e}")
#         response = "Sorry, something went wrong while processing your request."
    
#     save_message(chat_id, "TyrionAI", "bot", response)
#     logger.info(f"[Bot] TyrionAI: {response}")

#     for part in split_message(response):
#         await update.message.reply_text(part)



# Start bot
if __name__ == "__main__":
    logger.info("Starting bot...")
    app = Application.builder().token(TOKEN).build()
    
    # Set commands
    async def set_bot_commands():
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Provides help for the Tyrion bot"),
            BotCommand("starknet", "Brief information regarding Starknet"),
            BotCommand("staking", "Brief information regarding Staking"),
            BotCommand("crypto", "Brief information regarding Cryptocurrency"),
        ]
        await app.bot.set_my_commands(commands)
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("starknet", starknet_command))
    app.add_handler(CommandHandler("staking", staking_command))
    app.add_handler(CommandHandler("crypto", crypto_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Polling for updates...")
    app.run_polling(poll_interval=1)  # Faster response for interval =1 