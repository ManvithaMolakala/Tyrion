import spacy
from rapidfuzz import process, fuzz

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Define filter categories with synonyms
RISK_LEVELS = ["low", "medium", "high"]
RISK_SYNONYMS = {
    "low": ["low", "safe", "conservative", "minimal risk"],
    "medium": ["medium", "moderate", "balanced"],
    "high": ["high", "risky", "aggressive"]
}

PROTOCOL_TYPES = ["lending", "amm", "yield aggregators", "staking", "derivatives"]
PROTOCOL_SYNONYMS = {
    "lending": ["lending", "borrowing", "loan"],
    "amm": ["amm", "automated market maker", "dex"],
    "yield aggregators": ["yield aggregator", "yield farming", "auto-compound"],
    "staking": ["staking", "staked", "staking pool"],
    "derivatives": ["derivatives", "futures", "perpetuals"]
}

TVL_RANGES = {
    "low": ["under 10M", "small TVL", "low TVL"],
    "medium": ["100M", "500M", "medium TVL"],
    "high": ["1B", "above 1B", "high TVL"]
}

ASSETS = ["USDC", "ETH", "WBTC", "DAI", "STETH", "AVAX"]
AUDITED_KEYWORDS = ["audited", "secure", "verified"]
NON_AUDITED_KEYWORDS = ["unaudited", "risky", "unverified"]


def fuzzy_match(query, choices):
    """Find the closest match from a list of choices using fuzzy matching."""
    match, score = process.extractOne(query, choices, scorer=fuzz.ratio)
    return match if score > 70 else None  # Use 70% similarity threshold


def extract_filters(query):
    """Extracts filters like risk level, protocol type, TVL range, and assets from the user query."""
    doc = nlp(query.lower())
    filters = {}

    # Extract risk level
    for word in doc:
        for risk, synonyms in RISK_SYNONYMS.items():
            if word.text in synonyms:
                filters["risk"] = risk
                break

    # Extract protocol type
    for word in doc:
        for protocol, synonyms in PROTOCOL_SYNONYMS.items():
            if word.text in synonyms:
                filters["protocol_type"] = protocol.capitalize()
                break

    # Extract audited status
    if any(word.text in AUDITED_KEYWORDS for word in doc):
        filters["is_audited"] = True
    elif any(word.text in NON_AUDITED_KEYWORDS for word in doc):
        filters["is_audited"] = False

    # Extract TVL range
    for tvl_category, keywords in TVL_RANGES.items():
        for keyword in keywords:
            if keyword in query:
                filters["tvl_range"] = tvl_category
                break

    # Extract assets using fuzzy matching
    found_assets = [fuzzy_match(word.text.upper(), ASSETS) for word in doc if fuzzy_match(word.text.upper(), ASSETS)]
    if found_assets:
        filters["assets"] = list(set(found_assets))  # Remove duplicates

    return filters


# **Test Cases**
queries = [
    "Find me a conservative lending platform with over 1 billion TVL that supports USDC and ETH.",
    "Show me moderate-risk verified yield farming protocols with TVL in the 100M range.",
    "I want aggressive DeFi AMMs that have small TVL.",
    "Give me an unaudited staking protocol for ETH.",
]

for q in queries:
    print(f"Query: {q}")
    print("Extracted Filters:", extract_filters(q))
    print("-" * 50)
