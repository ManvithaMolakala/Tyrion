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
        
        response = filters_bot.invoke(statement)
        
        if not isinstance(response, str):
            raise ValueError("Unexpected response type from model.")

        # Clean up any potential unwanted tags
        return response

    except Exception as e:
        return f"Error: {str(e)}"

# # # Example Usage
# user_statement = "Please analyse the funds in my wallet '0xabcd' and suggest an investment strategy. I do not want to risk my funds but also not want to compromise on returns completely. Please look for a middle ground. Please suggest investment options."
# user_statement = "Give my wallet balance"
statement = "gm gm"
user_statement = f"""Generate response to the below prompt unless it is below two categories:
1.⁠ Investment_query (Investment suggestions, investment filters, etc.)
2.⁠ ⁠balance_query (Balance related queries)
If the prompt suits any of these categories, return just the category type. If not, generate a response as per your intelligence. 

Chat history:
User: gm gm
Bot: Good morning! How can I assist you today?

Next Prompt:
{statement}"""
result = classify_query(user_statement)
print("response:", result)
