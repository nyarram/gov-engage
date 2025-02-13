import requests
import json
import os
from dotenv import load_dotenv

# Load API keys
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

def google_search(query, num_results=10):
    """Uses Google Custom Search API to find recent news about a politician's promises."""
    search_results = []
    for start in range(1, num_results, 10):  # Fetch in batches of 10
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&start={start}&sort=date"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            break

        search_results.extend(response.json().get("items", []))

        if "items" not in response.json():  # Stop if no more results
            break

    return search_results

def track_promise_progress(politician, categorized_promises):
    """Searches for recent news articles tracking the progress of promises."""
    progress_tracking = {}

    for category, statements in categorized_promises.items():
        progress_tracking[category] = {}
        for statement in statements:
            search_query = f"{politician} {statement[:10]} progress"
            results = google_search(search_query)

            articles = [item["link"] for item in results]
            progress_tracking[category][statement] = articles[:5]  # Store top 5 sources

    return progress_tracking

# Load categorized promises
politician = "Narendra Modi"  # Change to test other politicians
with open(f"{politician}_categorized_promises.json", "r") as f:
    categorized_promises = json.load(f)

# Track progress
progress_tracking = track_promise_progress(politician, categorized_promises)

# Save results
with open(f"{politician}_progress.json", "w") as f:
    json.dump(progress_tracking, f, indent=4)

print(f"Saved progress tracking for {politician}")
