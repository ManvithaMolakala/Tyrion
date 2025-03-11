import ollama

# Initialise the Ollama client 
client = ollama.Client()

# Define the model and input prompt 
model = "Mistral"
prompt = "What is python?"

response = client.generate(model, prompt)

# print the response from the prompt
print(response.response)
 