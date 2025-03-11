import torch
import pickle
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
# from langchain_core.prompts import ChatPromptTemplate

# Load API key from .env file (not needed for local models but keeping for flexibility)
load_dotenv()

# Apple Silicon Optimization (MPS for Metal GPU)
device = torch.device("mps") if torch.backends.mps.is_available() else "cpu"

def load_and_prepare_data(file_path):
    """Loads and prepares text data for embedding."""
    loader = TextLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    print(f"Created {len(texts)} chunks of text.")
    return texts


def create_vector_store(texts):
    """Creates a FAISS vector store from text data."""
    embeddings = OllamaEmbeddings(model="Mistral", device = device)
    FAISS.omp_set_num_threads(6)  # Use multiple CPU threads for FAISS
    vector_store = FAISS.from_documents(texts, embeddings)
    print("Vector store created successfully!")
    return vector_store


def create_retriever(file_path):
    """Creates a retriever from text data."""
    texts = load_and_prepare_data(file_path)
    vector_store = create_vector_store(texts)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})   # default k = 4
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
    llm = OllamaLLM(model=selected_model, base_url = "http://localhost:11434", temperature = 0.1, device = device)

    # Define prompt template
    prompt_template = """
    You are "Tyrion," a friendly chatbot that helps users with questions about Starknet.

    How to Respond:
    If greeted with a "Hello" or "Hi," respond with a friendly greeting not extra information to be given.
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
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False,
            chain_type_kwargs={
            "prompt": prompt
            # "output_parser": StrOutputParser()
            },  # Ensures clean text output
        )

    return chatbot


# # Example Usage:
# chatbot = create_chatbot("data/combined_retriever.pkl", "model/meta-llama/Llama-3.2-1B")
# response = chatbot.invoke({"query": "What is the capital of India?"})
# print(response["result"])  # Instead of printing raw response object
