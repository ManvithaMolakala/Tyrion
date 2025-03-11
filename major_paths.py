import json

# Define paths for different files
paths = {
    "combined_scraped_text": "/Users/manvithamolakala/TyrionAI/data/combined_scraped_text.txt",
    "retriever": "/Users/manvithamolakala/TyrionAI/models/retriever.pkl",
    "chatbot": "/Users/manvithamolakala/TyrionAI/chatbot.py",
    "venv": "/Users/manvithamolakala/TyrionAI/.venv/lib/python3.9/site-packages/"
}

# Save paths to a JSON file
with open("paths.json", "w") as f:
    json.dump(paths, f, indent=4)

print("Paths saved successfully!")
