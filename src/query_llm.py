from langchain_ollama import OllamaLLM  
import re  

def classify_query(statement: str, model_name="mistral"):
    """Classifies the user's risk appetite based on their statement."""
    try:
        filters_bot = OllamaLLM(
            model=model_name,
            base_url="http://localhost:11434",  
            temperature=0.1  
        )
        
        response = filters_bot.invoke(f"If the query is about fetching balance just reply one-word response 'balance', similarly for investment related question reply one-word response 'investment' else respond to the question normally, like you would respond to any query. {statement}")
        
        if not isinstance(response, str):
            raise ValueError("Unexpected response type from model.")

        # Clean up any potential unwanted tags
        return response

    except Exception as e:
        return f"Error: {str(e)}"

# # # Example Usage
user_statement = "Please analyse the funds in my wallet '0xabcd' and suggest an investment strategy. I do not want to risk my funds but also not want to compromise on returns completely. Please look for a middle ground. Please suggest investment options."
user_statement = "Give my wallet balance"
user_statement = "gm"
result = classify_query(user_statement)
print("response:", result)
