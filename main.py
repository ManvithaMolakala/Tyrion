import time
from src.chatbot_ollama import create_chatbot  # Import your chatbot function

start_time = time.time()  # Start the timer
# Path to be checked after running the script "web_scrapping.py"
RETRIEVER_PATH = "src/data/combined_retriever.pkl"

# Initialize the chatbot with the JSON file
chatbot = create_chatbot(RETRIEVER_PATH)

mid_time  = time.time()
# Query the chatbot
response = chatbot.invoke({"query": "What is endur?"})
# response = chatbot.invoke("What is the starknet staking minting curve contract address on mainnet and reference link for the same?")

end_time = time.time()  # End the timer

# Print the chatbot response
print(response['result'])
# answer = response["result"].strip().split("\n")[-1]  # Get only the last line (the actual answer)
answer = response["result"].split("point):", 1)[-1].strip()

print(answer)
print(f"Time taken to create chatbot: {mid_time - start_time:.4f} seconds")
# Print the execution time
print(f"Total Execution Time: {end_time - start_time:.4f} seconds")
