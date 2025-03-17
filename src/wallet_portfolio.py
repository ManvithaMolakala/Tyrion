import asyncio
from typing import Dict
from starknet_py.contract import Contract
from starknet_py.net.full_node_client import FullNodeClient

# ✅ Starknet RPC provider (Testnet / Mainnet)
NODE_URL = "https://starknet-mainnet.public.blastapi.io/rpc/v0_7"  
client = FullNodeClient(node_url=NODE_URL)

# ✅ List of ERC-20 token contract addresses
PORTFOLIO_TOKENS = {
    "USDC": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    "ETH": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    "STRK": "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    "XSTRK": "0x028d709c875c0ceac3dce7065bec5328186dc89fe254527084d1689910954b0a"
}

# ✅ Token decimal places
TOKEN_DECIMALS = {
    "USDC": 6,   # USDC usually has 6 decimals
    "ETH": 18,   # ETH has 18 decimals
    "STRK": 18,  # STRK has 18 decimals
    "XSTRK": 18  # Assuming XSTRK also has 18 decimals
}

async def get_token_balances(contract_address: str) -> Dict[str, float]:
    """Fetches balances of all tracked ERC-20 tokens for a given contract address."""
    balances = {}
    contract_address = int(contract_address, 16)

    for token_name, token_address in PORTFOLIO_TOKENS.items():
        try:
            # Fetch contract ABI dynamically
            contract = await Contract.from_address(provider=client, address=token_address)

            # Fetch balance
            (balance,) = await contract.functions["balanceOf"].call(contract_address)
            
            # Convert to correct decimal format
            decimals = TOKEN_DECIMALS.get(token_name, 18)  # Default to 18 decimals if not found
            human_balance = balance / (10 ** decimals)

            # Store result
            balances[token_name] = human_balance
            print(f"{token_name} Balance: {human_balance:.6f}")  # Display up to 6 decimal places
        except Exception as e:
            print(f"Error fetching {token_name} balance: {e}")
            balances[token_name] = 0.0  # Default to 0 if there's an issue

    return balances

# async def main():
#     contract_address = "0x04cced5156ab726bf0e0ca2afeb1f521de0362e748b8bdf07857b088dbc7b457"
#     balances = await get_token_balances(contract_address)
#     print("\nFinal Token Balances:", balances)

# # Run the async function
# asyncio.run(main())
