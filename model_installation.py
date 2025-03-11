import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACEHUB_API_TOKEN")
# HUGGINGFACE_API_KEY = "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"
os.environ["HUGGINGFACEHUB_API_TOKEN"]=HUGGINGFACE_API_KEY

# model_name = "meta-llama/Llama-3.3-70B-Instructsz3"
model_name = "meta-llama/Llama-3.2-1B" # 1 Billion parameters

tokeniser = AutoTokenizer.from_pretrained(model_name, token = HUGGINGFACE_API_KEY)
model = AutoModelForCausalLM.from_pretrained(model_name, token = HUGGINGFACE_API_KEY)


tokeniser.save_pretrained(f"tokenisers/{model_name}")
model.save_pretrained(f"model/{model_name}") 

tokeniser = AutoTokenizer.from_pretrained(f"tokenisers/{model_name}")
model = AutoModelForCausalLM.from_pretrained(f"model/{model_name}")

prompt = "What is the capital of India?"

prompt_embeddings = tokeniser(prompt, return_tensors="pt") # pt means pytorch tensors

response = model.generate(**prompt_embeddings, max_length=500) # default max_new_tokens = 20

response_final = tokeniser.decode(response[0], skip_special_tokens=True)

print(response_final)



 