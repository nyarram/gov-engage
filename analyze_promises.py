import json
import spacy
from transformers import pipeline
from dotenv import load_dotenv
import os

# Load API keys (if needed for future AI models)
load_dotenv()

# Load NLP models
nlp = spacy.load("en_core_web_sm")
classifier = pipeline("zero-shot-classification")

# Define broad categories
CATEGORIES = [
    "Healthcare", "Economy", "Education", "Defense",
    "Environment", "Technology", "Infrastructure", "Social Welfare"
]

def categorize_promises(promises):
    """Categorizes promises into predefined categories using AI."""
    categorized = {category: [] for category in CATEGORIES}

    for entry in promises:
        for statement in entry["content"]:
            result = classifier(statement, CATEGORIES)
            top_category = result["labels"][0]  # Best-matching category
            categorized[top_category].append(statement)

    return categorized

# Load scraped promises
politician = "K. Chandrashekar Rao"  # Change this to test other politicians
with open(f"{politician}_promises.json", "r") as f:
    promises = json.load(f)

# Categorize promises
categorized_promises = categorize_promises(promises)

# Save results
with open(f"{politician}_categorized_promises.json", "w") as f:
    json.dump(categorized_promises, f, indent=4)

print(f"Saved categorized promises for {politician}")
