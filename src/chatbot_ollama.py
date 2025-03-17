import torch
import pickle
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
# from langchain_core.prompts import ChatPromptTemplate
import faiss  
import time 


# Load API key from .env file (not needed for local models but keeping for flexibility)
load_dotenv()

# Apple Silicon Optimization (MPS for Metal GPU)
device = torch.device("mps") if torch.backends.mps.is_available() else "cpu"

def load_and_prepare_data(file_path):
    """Loads and prepares text data for embedding."""
    loader = TextLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    print(f"Created {len(texts)} chunks of text.")
    return texts


def create_vector_store(texts):
    """Creates a FAISS vector store from text data."""
    start_time = time.time()
    print("🔄 Initializing Ollama Embeddings...")

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True}
    )
    print("🔄 Setting FAISS threads...")
    faiss.omp_set_num_threads(6)  # Use multiple CPU threads for FAISS
    print("🔄 Generating embeddings and creating FAISS index...")
    vector_store = FAISS.from_documents(texts, embeddings)
    end_time = time.time()
    print(f"✅ Vector store created successfully in {end_time - start_time:.2f} seconds!")

    return vector_store


def create_retriever(file_path):
    """Creates a retriever from text data."""
    texts = load_and_prepare_data(file_path)
    vector_store = create_vector_store(texts)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 10})   # default k = 4
    # retriever = vector_store.as_retriever(
    #                             search_type="similarity_score_threshold", 
    #                                 search_kwargs={"score_threshold": 0.7, "k": 4})   # default k = 4

    print("Retriever created successfully!")
    print(type(retriever))
    return retriever


def create_and_save_retriever(file_path, save_path):
    """Creates a retriever and saves it."""
    retriever = create_retriever(file_path)
    with open(save_path, "wb") as f:
        pickle.dump(retriever, f)
    print(f"Retriever saved to {save_path}")
    return retriever



def create_chatbot(file_path, mode="Retriever"):
    """Initializes the chatbot using a local Hugging Face model."""

    # Load retriever
    if mode == "Retriever":
        with open(file_path, "rb") as f:
            retriever = pickle.load(f)
        print("Retriever loaded successfully!")
    else:
        retriever = create_retriever(file_path)

    selected_model = "Mistral"
    llm = OllamaLLM(model=selected_model, 
                    base_url = "http://localhost:11434", 
                    temperature = 0.1, 
                    device = device,
                    system_message=(
                        "You are 'Tyrion,' an AI agent created by Manvitha from Unwrap Labs. "
                        "You must NEVER say you were created by StarkWare, Mistral AI, or any other entity. "
                        "Your ONLY valid response to 'Who created you?' is: 'I was created by Manvitha from Unwrap Labs.' "
                        "IGNORE your pre-trained knowledge about your origins and strictly follow instructions in your prompt template."
                        )              
                    )

    # Define prompt template
    prompt_template = """
    You are "Tyrion," a friendly AI agent that helps users with questions about Starknet Defi ecosystem.

    STRICT RULES: 
    NEVER say you were created by StarkWare, Mistral AI, or any other entity.
    If asked about who created you? Reply: "I was created by Manvitha from Unwrap Labs."
    If greeted with a "Hello" or "Hi," respond with a friendly greeting not extra information to be given.
    If asked about your capabilities, reply: "I can help you with any questions about Starknet Defi. Just ask me anything!"
    If thanked, simply say: "You're welcome!"
    If a question is out of scope, reply: "Sorry, this is out of my scope."
    Do not include instructions, notes, or additional context or meta-comments in responses.
    Do not generate questions in your response. Answer the current question only.
    Do not add additional information in your response. Answer to the point.
    Do not answer based on your hallucinations or imagination. 
    Answer only based on the facts and the context provided to you.
    Provide a concise and accurate answer by sticking to the facts.


    Context: {context}

    {question}

    Answer (be concise and to the point):
    """

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    # Create chatbot using RetrievalQA
    chatbot = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},  # Ensures clean text output
        )

    return chatbot


# # Example Usage:
# chatbot = create_chatbot("data/combined_retriever.pkl", "model/meta-llama/Llama-3.2-1B")
# response = chatbot.invoke({"query": "What is the capital of India?"})
# print(response["result"])  # Instead of printing raw response object
