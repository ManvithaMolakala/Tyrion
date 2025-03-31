from langchain_ollama import OllamaLLM  
import re  

def classify_risk(statement: str, model_name="deepseek-r1"):
    """Classifies the user's risk appetite based on their statement."""
    try:
        filters_bot = OllamaLLM(
            model=model_name,
            base_url="http://localhost:11434",  
            temperature=0.1  
        )

        query = f"""Analyze the following user statement and classify their risk appetite.  
        If the statement does not indicate any risk preference, classify it as "None."  
        Risk appetite categories: "low," "medium," "high," or "None."  

        Return only the risk category and a brief justification for your classification.  

        User statement: {statement}"""

        response = filters_bot.invoke(query)
        
        if not isinstance(response, str):
            raise ValueError("Unexpected response type from model.")

        # Clean up any potential unwanted tags
        cleaned_text = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        
        return cleaned_text

    except Exception as e:
        return f"Error: {str(e)}"

# Example Usage
user_statement = "Please analyse the funds in my wallet '0xabcd' and suggest an investment strategy. I do not want to risk my funds but also not want to compromise on returns completely. Please look for a middle ground. Please suggest investment options."
result = classify_risk(user_statement)
print(result)
