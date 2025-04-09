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

        query = f"""Analyze the following user statement and classify their risk profile, is_audited, protocols, min_tvl, assets, risk levels in a dictionary.  
        If the statement does not indicate any risk preference, classify it as "None."  
        Risk profile in plain text not list: "Risk averse," or "Balanced," or "Aggresive," or "None". 
        only if something is mentioned like only invest in low risk or only invest in high risk then classify it as ["low"], ["medium"] ["high"] = [risk_profile], Else []
        If the person mentions anything about only low risk or medium risk of protocols then classify it as risk_levels such as only low risk pools or only medium risk pools or low and medium risk pools return ["low"], ["medium"] ["low", "high"]= [risk_levels], Else [] 
        user will either mention his risk profile or about the risk levels of the protocols. but not both. One is investment thesis and the other is just saying invest only in this risk levels. based on risk profile portfolio will be created.
        So in summary always one of the risk profile or risk levels will be []. both can be non empty simultaneously.
        If the person mentions anything about only audited protocols then classify it as is_audited = true, Else false 
        If the person mentions anything about only specific protocols then classify it as protocols such as only vesu, only strkfarm, only endur etc like = ["vesu"] etc, Else []
        If the person mentions anything about only specific TVL then classify it as tvl = [tvl], Else 0
        If the person mentions anything about greater than a specific apy then classify it as apy = [apy], Else []
        Only if the person mentions anything about invest only specific assets/tokens (example strk, ETH, wbtc, xstrk, etc, you can identify by keywords token or asset) then classify it as assets = [assets] do not write your own token just extract, if nothing is mentioned then assign [] 
        Return the risk profile, is_audited, protocols, min_tvl, assets, risk levels in dictionary.  
        return a single json. last sentence is current user statement and previous user conversation. 

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
