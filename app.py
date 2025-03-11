from fastapi import FastAPI
from pydantic import BaseModel
from chatbot import create_chatbot

# Initialize FastAPI app
app = FastAPI()

# Load chatbot
chatbot = create_chatbot("data/starknet_docs.txt")

class Query(BaseModel):
    question: str

@app.post("/chat")
def chat(query: Query):
    response = chatbot.run(query.question)
    return {"response": response}

# Run using: uvicorn app:app --reload
