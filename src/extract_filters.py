from langchain_ollama import OllamaLLM  
import re  

model_name = "deepseek-r1"
# model_name = "mistral"

def classify_risk(statement: str, model_name=model_name):
    """Classifies the user's risk appetite based on their statement."""
    try:
        filters_bot = OllamaLLM(
            model=model_name,
            base_url="http://localhost:11434",  
            temperature=0.1  
        )

        query = f"""Analyze the following user statement and classify the user's investment preferences into the following categories, and return the result in a single JSON object:

        - `risk_profile`: One of `"Risk averse"`, `"Balanced"`, `"Aggressive"`, or `"None"` (plain text, not a list). Use `"Risk averse"` if the user mentions only low-risk investments, `"Balanced"` for a mix, and `"Aggressive"` if the user prefers high-risk opportunities. If no preference is mentioned, use `"None"`.

        - `risk_levels`: Use this only if the user specifies preferences for *protocol risk levels* (e.g., "only low risk pools", "medium risk protocols"). Values must be from: `["low"]`, `["medium"]`, or combinations like `["low", "medium"]`. If nothing is mentioned, return an empty list `[]`.

        - Note: Only one of `risk_profile` or `risk_levels` will be non-empty. If one is set, the other must be empty.

        - `is_audited`: `true` if the user specifies "only audited protocols", else `false`.

        - `protocols`: List of specific protocols mentioned (e.g., `["vesu"]`, `["strkfarm"]`, ["endur]). If none are mentioned, return an empty list `[]`.

        - `min_tvl`: A number if the user mentions a minimum TVL (e.g., "only protocols with TVL over 1M"), otherwise return `0`.

        - `apy`: A number if the user mentions minimum APY (e.g., "only if APY is over 15%"), otherwise return 0.

        - `assets`: List of specific assets or tokens mentioned (e.g., `["USDC","STRK","ETH", "wBTC", "xSTRK"]`). Only include tokens mentioned explicitly using keywords like "token" or "asset". Otherwise, return `[]`.

        Return the result as a single JSON object. The last sentence is the **current user statement**, with previous conversation context included if applicable.

        User statement: {statement}"""

        # and a brief justification for your classification
        
        response = filters_bot.invoke(query)
        
        if not isinstance(response, str):
            raise ValueError("Unexpected response type from model.")

        # Clean up any potential unwanted tags
        cleaned_text = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        print(cleaned_text)
        return cleaned_text

    except Exception as e:
        return f"Error: {str(e)}"

# # # Example Usage
# user_statement = "Please analyse the funds in my wallet '0xabcd' and suggest an investment strategy. I do not want to risk my funds but also not want to compromise on returns completely. Please look for a middle ground. Please suggest investment options."
# result = classify_risk(user_statement)
# print(result)
