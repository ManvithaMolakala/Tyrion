import asyncio
from typing import Dict
from starknet_py.contract import Contract
from starknet_py.net.full_node_client import FullNodeClient
from dotenv import load_dotenv
import os

# ✅ Starknet RPC provider (Testnet / Mainnet)
load_dotenv()
NODE_URL = os.getenv("STARKNET_RPC_PROVIDER")  
client = FullNodeClient(node_url=NODE_URL)

# ✅ List of ERC-20 token contract addresses
PORTFOLIO_TOKENS = {
    "USDC": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    "ETH": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    "STRK": "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    "XSTRK": "0x028d709c875c0ceac3dce7065bec5328186dc89fe254527084d1689910954b0a",
    # "USDT": "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    # "ZEND": "0x02a28036ec5007c05c5611281a7d740c71a26d0305f7e9a4fa2f751d252a9f0d",
    # "WBTC": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    # "NSTSTRK": "0x03e3c4b9e256b07ba29a35e58fc556ac55fc7cfeb6dab85717755ec5e712b8d5",
    # "DAI": "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    # "EKUBO": "0x075afe6402ad5a5c20dd25e10ec3b3986acaa647b77e4ae24b0cbc9a54a27a87",
    # "LUSD": "0x070a76fd48ca0ef910631754d77dd822147fe98a569b826ec85e3c33fde586ac",
    # "LORD": "0x0124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49",
    "WSTETH": "0x0057912720381af14b0e5c87aa4718ed5e527eab60b3801ebf702ab09139e38b",
    # "UNI": "0x049210ffc442172463f3177147c1aeaa36c51d152c1b0630f2364c300d4f48ee",
    # "NSTRK": "0x07c535ddb7bf3d3cb7c033bd1a4c3aac02927a4832da795606c0f3dbbc6efd17",
    # "RETH": "0x0319111a5037cbec2b3e638cc34a3474e2d2608299f3e62866e9cc683208c610",
    # "SWAY": "0x04480b2ab159bd1da5e2ba802d1ffb2d8ba076a675dc445435fca19b1e360f21",
    # "SSTRK": "0x0260c02fd6942c788b8905d2c1b98b5a98fffd2ec0dfb013aa4b148781e269b6",
    # "BRRR": "0x67737cbee9be3e3042ca86ef41598af7cc36fa6e109193c165b854de07d1df7",
    # "TONY":"0x5f467ace847d1cbc6d1efea978752a8b4549fec043286fec1289d19b8c57e67",
    # "AKU": "0x137dfca7d96cdd526d13a63176454f35c691f55837497448fad352643cfe4d4",
    # "UNO":"0x719b5092403233201aa822ce928bd4b551d0cdb071a724edd7dc5e5f57b7f34"
}

# ✅ Token decimal places
TOKEN_DECIMALS = {
    "USDC": 6,   # USDC usually has 6 decimals
    "ETH": 18,   # ETH has 18 decimals
    "STRK": 18,  # STRK has 18 decimals
    "XSTRK": 18,  # XSTRK has 18 decimals
    "USDT": 6,   # USDT usually has 6 decimals
    # "ZEND": 18,  # ZEND has 18 decimals
    "WBTC": 8,   # WBTC usually has 8 decimals
    "NSTSTRK": 18,  # nstSTRK has 18 decimals
    "DAI": 18,  # DAI has 18 decimals
    "LUSD": 18,  # LUSD has 18 decimals
    "LORD": 18,  # LORD has 18 decimals
    "EKUBO": 18,  # EKUBO has 18 decimals
    "WSTETH": 18,  # WETH has 18 decimals
    "UNI": 18,  # UNI has 18 decimals
    "NSTRK": 18,  # NSTRK has 18 decimals
    "RETH": 18,  # rETH has 18 decimals
    "SWAY": 18,  # SWAY has 18 decimals
    "vSTRK": 18,  # vSTRK has 18 decimals
    "SSTRK": 18,  # sSTRK has 18 decimals
    "BRRR": 18,  # BRRR has 18 decimals
    "TONY": 18,  # TONY has 18 decimals
    "AKU": 18,  # AKU has 18 decimals
    "UNO": 18,  # UNO has 18 decimals

}

async def fetch_balance(token_name: str, token_address: str, contract_address: int) -> tuple:
    """Fetches the balance for a single token asynchronously."""
    try:
        contract = await Contract.from_address(provider=client, address=token_address)
        (balance,) = await contract.functions["balanceOf"].call(contract_address)
        
        decimals = TOKEN_DECIMALS.get(token_name, 18)
        human_balance = balance / (10 ** decimals)

        return token_name, human_balance
    
    except Exception as e:
        print(f"Error fetching {token_name} balance: {e}")
        return token_name, 0.0
    
# TO DO: Reduce time taken to get token balances 
async def get_token_balances(contract_address: str) -> str:
    """Fetches balances of all tracked ERC-20 tokens, skipping zero-value balances."""
    contract_address = int(contract_address, 16)

    # Fetch balances concurrently
    results = await asyncio.gather(
        *(fetch_balance(token_name, token_address, contract_address) for token_name, token_address in PORTFOLIO_TOKENS.items())
    )

    # Filter out tokens with zero balance
    non_zero_balances = [(token, balance) for token, balance in results if balance > 0]

    # Format the output
    balance_str = "\n".join(f"{token}: {balance:.6f}" for token, balance in non_zero_balances)

    return "Wallet portfolio: \n" + balance_str if balance_str else "No tokens with balance found."

async def get_token_balances_dict(contract_address: str) -> dict:
    """Fetches balances of all tracked ERC-20 tokens, skipping zero-value balances."""
    contract_address = int(contract_address, 16)

    # Fetch balances concurrently
    results = await asyncio.gather(
        *(fetch_balance(token_name, token_address, contract_address) for token_name, token_address in PORTFOLIO_TOKENS.items())
    )

    # Filter out tokens with zero balance
    non_zero_balances = {token: balance for token, balance in results if balance > 0}

    return non_zero_balances  # Returns as a dictionary


# async def main():
#     contract_address = "0x04cced5156ab726bf0e0ca2afeb1f521de0362e748b8bdf07857b088dbc7b457"
#     balances = await get_token_balances(contract_address)
#     print("\nFinal Token Balances:", balances)

# # Run the async function
# asyncio.run(main())
