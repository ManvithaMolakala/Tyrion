import torch
import pickle
import time
import requests
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import faiss  

# Load API key from .env file (not needed for local models but keeping for flexibility)
load_dotenv()

# Apple Silicon Optimization (MPS for Metal GPU)
device = torch.device("mps") if torch.backends.mps.is_available() else "cpu"


def load_and_prepare_data(file_path):
    """Loads and prepares text data for embedding."""
    loader = TextLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    texts = text_splitter.split_documents(documents)
    print(f"✅ Created {len(texts)} chunks of text.")
    return texts


def create_vector_store(texts):
    """Creates a FAISS vector store from text data."""
    start_time = time.time()

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True}
    )

    faiss.omp_set_num_threads(6)  # Use multiple CPU threads for FAISS
    vector_store = FAISS.from_documents(texts, embeddings)

    print(f"✅ Vector store created in {time.time() - start_time:.2f} seconds!")
    return vector_store


def create_retriever(file_path):
    """Creates a retriever from text data."""
    texts = load_and_prepare_data(file_path)
    vector_store = create_vector_store(texts)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    print("✅ Retriever created successfully!")
    return retriever


def create_and_save_retriever(file_path, save_path):
    """Creates a retriever and saves it."""
    retriever = create_retriever(file_path)
    with open(save_path, "wb") as f:
        pickle.dump(retriever, f)
    print(f"✅ Retriever saved to {save_path}")
    return retriever


def fetch_tvl_data():
    """Fetches real-time TVL data from DeFiLlama API."""
    url = "https://api.llama.fi/chains"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error if API request fails
        data = response.json()

        tvl_data = {chain["name"].lower(): f"${chain['tvl'] / 1e6:.1f}M" for chain in data if chain.get("tvl")}
        print("✅ TVL data fetched successfully!")
        return tvl_data
    
    except requests.RequestException as e:
        print(f"❌ Error fetching TVL data: {e}")
        return {}


class StarknetChatbot:
    """Wrapper around RetrievalQA to handle TVL queries separately."""

    def __init__(self, retriever):
        self.tvl_data = fetch_tvl_data()
        selected_model = "Mistral"

        # Initialize LLM
        self.llm = OllamaLLM(model=selected_model, base_url="http://localhost:11434", temperature=0.1)

        # Define prompt template
        prompt_template = """
        You are "Tyrion," a friendly chatbot that helps users with questions about the Starknet DeFi ecosystem.

        How to Respond:
        - If asked about TVL (Total Value Locked), provide the value formatted as "$X.XM".
        - If a question is out of scope, reply: "Sorry, this is out of my scope."
        - Keep responses concise.

        Context: {context}

        {question}

        Answer:
        """

        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

        # Create RetrievalQA chatbot
        self.retrieval_qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

    def process_query(self, query):
        """Intercepts TVL queries and fetches data if needed."""
        query_text = query["query"] if isinstance(query, dict) else str(query)  # Ensure string
        lower_query = query_text.lower()

        # Check if query is about TVL
        if "tvl" in lower_query or "total value locked" in lower_query:
            for protocol in self.tvl_data.keys():
                if protocol in lower_query:
                    return f"The TVL of {protocol.capitalize()} is {self.tvl_data[protocol]}."
            return "Sorry, I couldn't find the TVL data for that protocol."

        # Otherwise, use RetrievalQA
        response = self.retrieval_qa.invoke({"query": query})
        return response["result"]


def create_chatbot(file_path, mode="Retriever"):
    """Initializes the chatbot and handles TVL queries separately."""
    
    # Load retriever
    if mode == "Retriever":
        with open(file_path, "rb") as f:
            retriever = pickle.load(f)
        print("✅ Retriever loaded successfully!")
    else:
        retriever = create_retriever(file_path)

    return StarknetChatbot(retriever)


# # Example Usage:
# chatbot = create_chatbot("data/combined_retriever.pkl")
# response = chatbot.process_query("What is the TVL of Starknet?")
# print(response)  # Example output: "The TVL of Starknet is $XXX.XM."
