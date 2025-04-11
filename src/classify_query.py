from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import numpy as np

# Step 1: Use a compact sentence transformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# Step 2: Training examples
examples = [
    ("What is the current market value of my tokens?", "balance"),
    ("What is the status of my crypto assets?", "balance"),
    ("Show me my contract address balance", "balance"),
    ("What is the liquidity of my assets?", "balance"),
    ("How much money do I have?", "balance"),
    ("What's the total value of my assets?", "balance"),
    ("What are my token balances?", "balance"),
    ("How much ETH do I own?", "balance"),
    ("Tell me about my portfolio", "balance"),
    ("How do I check my token balances?", "balance"),
    ("Tokens in my account", "balance"),
    ("What is my total asset value?", "balance"),
    ("How do I check my balance?", "balance"),
    ("What is the current value of my tokens?", "balance"),
    ("What is my current balance?", "balance"),
    ("How can I track my assets?", "balance"),
    ("Can you show me my holdings?", "balance"),

    ("Give me investment advice", "investment"),
    ("What are the top-performing assets?", "investment"),
    ("How can I diversify my portfolio?", "investment"),
    ("Maximize yield of my tokens", "investment"),
    ("Show me my investment options", "investment"),
    ("How to optimize my crypto investments?", "investment"), 
    ("What are the best strategies for yield farming?", "investment"),
    ("How do I maximize my crypto yield?", "investment"),
    ("What is the performance of my investments?", "investment"),
    ("What are the best investment options?", "investment"),
    ("What are the latest investment trends?", "investment"),
    ("How can I improve my investment returns?", "investment"),
    ("Can you help me with investment strategies?", "investment"),
    ("How do I analyze my portfolio?", "investment"),
    ("What are the risks associated with my investments?", "investment"),
    ("How can I increase my asset value?", "investment"),
    ("What is the yield on my investments?", "investment"),
    ("How do I manage my crypto portfolio?", "investment"),
    ("What are the best practices for crypto investing?", "investment"),
    ("How can I evaluate my investment performance?", "investment"),
    ("What should I invest in right now?", "investment"),
    ("How can I increase my yield?", "investment"),
    ("How do I assess my investment strategy?", "investment"),
    ("What are the most profitable assets?", "investment"),
    ("How can I rebalance my portfolio?", "investment"),
    ("How do I track my investment performance?", "investment"),
    ("What are the top investment opportunities?", "investment"),
    ("How can I minimize my investment risks?", "investment"),
    ("What is the potential return on my investments?", "investment"),
    ("How do I optimize my asset allocation?", "investment"),
    ("What are the key metrics for evaluating investments?", "investment"),
    ("How can I stay updated on market trends?", "investment"),
    ("What is the best way to invest in crypto?", "investment"),
    ("0x04cced5156ab726bf0e0ca2afeb1f521de0362e748b8bdf07857b088dbc7b457  update to only vesu protocols investments", "investment"),
    # ("Hi", "other"),
    # ("Hello", "other"),
    # ("Goodbye", "other"),
    # ("Thanks", "other"),
    # ("What is your name?", "other"),
    # ("Can you help me?", "other"),
    # ("Tell me a joke", "other"),
    # ("What is the weather like?", "other"),
    # ("How are you?", "other"),
    # ("What is your favorite color?", "other"),
    # ("Do you like music?", "other"),
    # ("What is your hobby?", "other"),
    # ("Can you play a game?", "other"),
    # ("What is your favorite food?", "other"),
    # ("Tell me a story", "other"),
    # ("What is your favorite movie?", "other"),
    # ("What is your favorite book?", "other"),
    # ("Can you sing?", "other"),
    # ("What is your favorite sport?", "other"),
    # ("Do you have any pets?", "other"),
    # ("What is your favorite season?", "other"),
    # ("Can you dance?", "other"),
    # ("What is your favorite place to visit?", "other"),
    # ("What is your dream job?", "other"),
    # ("Do you like to travel?", "other"),
    # ("What is your favorite animal?", "other"),
    # ("Can you tell me a secret?", "other"),
    # ("What is your favorite holiday?", "other"),
    # ("What is Starknet", "other"),
    # ("What is Ethereum", "other"),
    # ("What is Bitcoin", "other"),
    # ("What is a blockchain", "other"),
    # ("What is a smart contract", "other"),
    # ("What is DeFi", "other"),
    # ("What is a token", "other"),
    # ("What is a wallet", "other"),
    # ("What is a DApp", "other"),
    # ("What is a DAO", "other"),
    # ("What is a cryptocurrency", "other"),
    # ("What is an NFT", "other"),
    # ("What is yield farming", "other"),
    # ("What is liquidity mining", "other"),
    # ("What is staking", "other"),
    # ("What is a liquidity pool", "other"),
    # ("What is a decentralized exchange", "other"),
    # ("What is a centralized exchange", "other"),
    # ("What is a market maker", "other"),
    # ("What is a market taker", "other"),
    # ("What is a limit order", "other"),
    # ("What is a market order", "other"),
    # ("What is a stop loss order", "other"),
    # ("What is a take profit order", "other"),
    # ("What is a candlestick chart", "other"),
    # ("What is a trading strategy", "other"),
    # ("What is technical analysis", "other"),
    # ("What is fundamental analysis", "other"),
    # ("What is sentiment analysis", "other"),
    # ("What is a trading bot", "other"),
    # ("What is algorithmic trading", "other"),
    # ("What is high-frequency trading", "other"),
    # ("What is a trading signal", "other"),
    # ("What is a trading indicator", "other"),
    # ("What is a trading platform", "other"),
    # ("What is a trading account", "other"),
    # ("What is a trading fee", "other"),
    # ("What is a trading pair", "other"),
    # ("What is a trading volume", "other"),
    # ("What is a trading history", "other"),
    # ("What is a trading journal", "other"),
]

# Step 3: Prepare data
X_train = model.encode([x[0] for x in examples])
y_train = [x[1] for x in examples]

# Step 4: Train classifier
clf = LogisticRegression()
clf.fit(X_train, y_train)

# Function to classify new text
def classify_query(text):
    embedding = model.encode([text])
    prediction = clf.predict(embedding)
    return prediction[0]

# Example
print(classify_query("suggest where to put my tokens"))  # investment
print(classify_query("Tokens in my account"))           # balance
print(classify_query("What is Starknet"))                # other
