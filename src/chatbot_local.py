import os
import pickle
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import multiprocessing
print("CPU cores available:", multiprocessing.cpu_count())


# Load API key from .env file (not needed for local models but keeping for flexibility)
load_dotenv()


def load_and_prepare_data(file_path):
    """Loads and prepares text data for embedding."""
    loader = TextLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    return texts


def create_vector_store(texts):
    """Creates a FAISS vector store from text data."""
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    vector_store = FAISS.from_documents(texts, embeddings)
    return vector_store


def create_retriever(file_path):
    """Creates a retriever from text data."""
    texts = load_and_prepare_data(file_path)
    vector_store = create_vector_store(texts)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})   # default k = 4
    return retriever


def create_and_save_retriever(file_path, save_path):
    """Creates a retriever and saves it."""
    retriever = create_retriever(file_path)
    with open(save_path, "wb") as f:
        pickle.dump(retriever, f)
    print(f"Retriever saved to {save_path}")
    return retriever


def create_chatbot(file_path, model_path, mode="Retriever"):
    """Initializes the chatbot using a local Hugging Face model."""

    # Load retriever
    if mode == "Retriever":
        with open(file_path, "rb") as f:
            retriever = pickle.load(f)
        print("Retriever loaded successfully!")
    else:
        retriever = create_retriever(file_path)

    # Determine device (MPS for Mac, CUDA for Nvidia, otherwise CPU)
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load local model and tokenizer
    print(f"Loading local model on {device}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map=device)

    # Create text generation pipeline with HuggingFacePipeline (Fix for LangChain)
    text_gen_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=500,
        do_sample=False,  # Uses greedy decoding
        repetition_penalty=1.2,
        eos_token_id=tokenizer.eos_token_id
    )


    llm = HuggingFacePipeline(pipeline=text_gen_pipeline)

    # Define prompt template
    prompt_template = """
    You are "Tyrion," a friendly chatbot that helps users with questions about Starknet.

    How to Respond:
    If asked about who created you? Reply: "I was created by Manvitha from Unwrap Labs."
    If asked about your capabilities, reply: "I can help you with any questions about Starknet. Just ask me anything!"
    If greeted, respond with a friendly greeting.
    If thanked, simply say: "You're welcome!"
    If asked a question, provide a concise and accurate answer.
    If a question is out of scope, reply: "Sorry, this is out of my scope."
    Do not add explanations about how you generate responses or refer to conversation history unless necessary.
    If a query is related to TVL (Total Value Locked), format the value as "$X.XM" (e.g., "$100M").

    Additional Rules:
    Do not include instructions, notes, or additional context or meta-comments in responses.
    Do not mention your creator unless explicitly asked.
    Do not provide personal opinions or anecdotes.
    Do not provide financial advice or predictions.
    Do not use slang, jargon, or emojis.
    Do not share previous conversation with the user unless necessary.
    Do not generate questions in your response. Answer the current question only.

    Context: {context}

    {question}

    Answer (be concise and to the point):
    """

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    # Create chatbot using RetrievalQA
    chatbot = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=False, chain_type_kwargs={"prompt": prompt})

    return chatbot


# # Example Usage:
# chatbot = create_chatbot("data/combined_retriever.pkl", "model/meta-llama/Llama-3.2-1B")
# response = chatbot.invoke({"query": "What is the capital of India?"})
# print(response["result"])  # Instead of printing raw response object
