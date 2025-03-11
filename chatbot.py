import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.llms import HuggingFaceHub
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import pickle


# Load API key from .env file
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACEHUB_API_TOKEN")
# HUGGINGFACE_API_KEY = "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"
os.environ["HUGGINGFACEHUB_API_TOKEN"]=HUGGINGFACE_API_KEY


if not HUGGINGFACE_API_KEY:
    raise ValueError("API key not found! Set it in a .env file or environment variables.")


def load_and_prepare_data(file_path):
    """Loads and prepares text data for embedding."""
    loader = TextLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    return texts

def create_vector_store(texts):
    """Creates a FAISS vector store from text data."""
    embeddings=HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",      #sentence-transformers/all-MiniLM-l6-v2
        model_kwargs={'device':'cpu'},
        encode_kwargs={'normalize_embeddings':True}
    )
    vector_store = FAISS.from_documents(texts, embeddings)
    return vector_store

def create_retriever(file_path):
    """Creates a retriever from text data."""
    texts = load_and_prepare_data(file_path)
    vector_store = create_vector_store(texts)
    retriever = vector_store.as_retriever(search_type="similarity")
    return retriever

def create_and_save_retriever(file_path, save_path):
    """Creates a retriever and saves it."""
    retriever = create_retriever(file_path)
     # Save retriever to a .pkl file
    with open(save_path, "wb") as f:
        pickle.dump(retriever, f)
    print(f"Retriever saved to {save_path}")
    return retriever

def create_chatbot(file_path, mode="Retriever"):

    """Initializes the chatbot using Hugging Face models."""
    if mode == "Retriever":
        with open(file_path, "rb") as f:
            retriever = pickle.load(f)
        print("Retriever loaded successfully!")
    else:
        retriever = create_retriever(file_path)

    llm = HuggingFaceHub(repo_id="mistralai/Mistral-7B-Instruct-v0.2", model_kwargs={"temperature":0.1,"max_length":500})
    prompt_template="""
    You are "Tyrion," a friendly chatbot that helps users with questions about Starknet.

    How to Respond:
    If asked about who created you? Reply: "I was created by Manvitha from Unwrap labs."
    If asked about your capabilities, reply: "I can help you with any questions about Starknet. Just ask me anything!"
    If greeted, respond with a friendly greeting.
    If thanked, simply say: "You're welcome!"
    If asked a question, provide a concise and accurate answer.
    If a question is out of scope, reply: "Sorry, this is out of my scope."
    Do not add explanations about how you generate responses or refer to conversation history unless necessary.
    If a query is related to TVL (Total Value Locked), format the value as "$X.XM" (e.g., "$100M").

    Additional Rules:
    Do not include instructions or note or additional context or meta-comments in responses.
    Do not mention your creator unless explicitly asked.
    Do not provide personal opinions or anecdotes.
    Do not provide financial advice or predictions.
    Do not use slang, jargon, or emojis.

    Context:{context}

    {question}

    Answer (be concise and to the point):
    """    

    prompt=PromptTemplate(template=prompt_template,input_variables=["context","question"])

    # Create the chatbot using RetrievalQA with proper arguments
    chatbot = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=False, chain_type_kwargs={"prompt":prompt})
    
    return chatbot