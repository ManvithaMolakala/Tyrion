from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from chatbot_ollama import create_chatbot
import logging
import os
import sqlite3

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Load bot token securely
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("Missing TELEGRAM_BOT_TOKEN. Set it as an environment variable.")
    exit(1)

BOT_USERNAME = "@TyrionAibot"


# Initialize the chatbot
RETRIEVER_PATH = "data/combined_retriever.pkl"
# chatbot = create_chatbot(RETRIEVER_PATH, path_to_local_model)
chatbot = create_chatbot(RETRIEVER_PATH)

logger.info("Chatbot initialized")

# Initialize SQLite database
DB_PATH = "data/chat_history.db"

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
        WHERE chat_id = ? 
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

# Function to handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        logger.warning("Received an update without a text message.")
        return
    
    text = update.message.text
    chat_id = update.message.chat.id
    user = update.message.from_user
    username = user.username or user.first_name or user.last_name or f"User_{user.id}"

    logger.info(f"[User] {username}: {text}")

    previous_conversation = get_last_messages(chat_id, limit=2)
    save_message(chat_id, username, "user", text)

    full_prompt = f"I am sharing our previous conversation here: \n\n Previous conversation: \n{previous_conversation}. \n\n Use the previous conversation to answer my question only if the user is asking a follow-up question or is referring to the previous question. Else ignore the previous conversation and answer only the current question. \n Here is the New question: {text}. \n Bot:"
    # full_prompt = text
    print("full prompt:", full_prompt)
    try:
        entire_response = chatbot.invoke({"query": full_prompt})
        response = entire_response["result"].split("point):", 1)[-1].strip()
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        response = "Sorry, something went wrong while processing your request."
    
    save_message(chat_id, "TyrionAI", "bot", response)
    logger.info(f"[Bot] TyrionAI: {response}")

    for part in split_message(response):
        await update.message.reply_text(part)

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