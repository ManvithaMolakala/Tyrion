from langchain_ollama import OllamaLLM  
import re  

def output_bot(response: str, model_name="deepseek-r1") -> str:
    filters_bot = OllamaLLM(
        model=model_name,
        base_url="http://localhost:11434",  
        temperature=0.1  
    )

    prompt = f"""Please use the information given to you in order to send it to the user in a more human-like way withoput markdown. 
    Please make sure to include the following information in your response:
    {response}"""
    
    return filters_bot.invoke(prompt)


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
        Risk appetite categories: "Risk averse," "Balanced," "Aggresive," or "None."  

        Return only the risk category.  

        User statement: {statement}"""
        
        # and a brief justification for your classification
        
        response = filters_bot.invoke(query)
        
        if not isinstance(response, str):
            raise ValueError("Unexpected response type from model.")

        # Clean up any potential unwanted tags
        cleaned_text = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        
        return cleaned_text

    except Exception as e:
        return f"Error: {str(e)}"

# # Example Usage
# user_statement = "Please analyse the funds in my wallet '0xabcd' and suggest an investment strategy. I do not want to risk my funds but also not want to compromise on returns completely. Please look for a middle ground. Please suggest investment options."
# result = classify_risk(user_statement)
# print(result)
