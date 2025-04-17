from langchain_ollama import OllamaLLM
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def classify_query(statement: str, model_name: str = "mistral", base_url: str = "http://localhost:11434") -> str:
    """
    Classifies a user query into one of the following categories:
    - investment_query
    - balance_query
    - other_query (with a model-generated response)

    Parameters:
    - statement (str): The user's input statement.
    - model_name (str): The name of the local model to use.
    - base_url (str): The base URL of the Ollama server.

    Returns:
    - str: The classification category, and optionally a model response.
    """
    try:
        llm = OllamaLLM(
            model=model_name,
            base_url=base_url,
            temperature=0.1
        )

        prompt = f"""
You are a smart assistant designed to classify user queries into one of three categories:

1. investment_query — Queries asking for contract addresses, investment suggestions, or investment filters.
2. balance_query — Queries asking for wallet balance or related information.
3. other_query — Any queries that don't fall into the above two.

Instructions:
- If the input clearly falls into 'investment_query' or 'balance_query', respond with just the category name.
- If it's 'other_query', respond with the category name and a helpful, intelligent reply.

User Query:
{statement}
"""

        logger.info("Sending prompt to model:\n%s", prompt)

        response = llm.invoke(prompt)

        if not isinstance(response, str):
            raise ValueError("Unexpected response type from model.")

        response = response.strip().lower()

        # Validate the start of the response
        match = re.match(r"^(investment_query|balance_query|other_query)", response)
        if match:
            return response
        else:
            return f"Unexpected model response format: {response}"

    except Exception as e:
        logger.error("Error during classification: %s", str(e))
        return f"Error: {str(e)}"


# === Example Usage ===
# if __name__ == "__main__":
#     test_statements = [
#         "give investment suggestion for my wallet 0x1234567890abcdef1234567890abcdef12345678",
#         "What's my wallet balance?",
#         "How's the weather today?",
#     ]

#     for stmt in test_statements:
#         print(f"\nInput: {stmt}")
#         result = classify_query(stmt)
#         print("Response:", result)
