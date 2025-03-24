import openai
import requests

API_KEY = "your_openai_api_key"

# Function to fetch APY data from DeFiLlama
def get_best_apy():
    url = "https://yields.llama.fi/pools"
    response = requests.get(url).json()
    
    top_pools = sorted(response['data'], key=lambda x: x['apy'], reverse=True)[:3]
    
    return [{"Protocol": p['project'], "APY": f"{p['apy']}%", "Asset": p['symbol']} for p in top_pools]

# Example user wallet data
wallet_data = {
    "ETH_balance": "1.2 ETH",
    "USDC_balance": "500 USDC"
}

# Fetch the best APY opportunities
apy_data = get_best_apy()

# Prepare the LLM prompt
context = f"""
The user has the following crypto balances:
- ETH: {wallet_data['ETH_balance']}
- USDC: {wallet_data['USDC_balance']}

The best staking opportunities available:
- {apy_data[0]['Protocol']}: {apy_data[0]['APY']} APY for {apy_data[0]['Asset']}
- {apy_data[1]['Protocol']}: {apy_data[1]['APY']} APY for {apy_data[1]['Asset']}
- {apy_data[2]['Protocol']}: {apy_data[2]['APY']} APY for {apy_data[2]['Asset']}

Suggest the best investment strategy based on this data.
"""

# Send the prompt to GPT-4
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a crypto investment assistant."},
        {"role": "user", "content": context}
    ],
    api_key=API_KEY
)

# Print the response
print(response['choices'][0]['message']['content'])
