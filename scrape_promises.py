import requests
import json
import os
import re
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load API Keys from .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

def google_search(query, num_results=30):
    """Uses Google Custom Search API to fetch more results."""
    search_results = []
    for start in range(1, num_results, 10):  # Fetch in batches of 10
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&start={start}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            break

        search_results.extend(response.json().get("items", []))

        if "items" not in response.json():  # Stop if no more results
            break

    return search_results

def extract_relevant_statements(html_content, politician_name):
    """Extracts all statements that mention the politician's name or political phrases."""
    soup = BeautifulSoup(html_content, "html.parser")
    text_elements = soup.find_all(["p", "h1", "h2", "h3", "li", "blockquote"])  # Extract from multiple tags
    
    relevant_statements = []
    for element in text_elements:
        text = element.get_text().strip()
        
        # Look for mentions of the politician's name or political keywords
        if politician_name.lower() in text.lower() or re.search(r'\b(reform|initiative|announcement|pledge|agenda|manifesto|government|policy|development|growth|budget|speech|election|promises|strategy)\b', text, re.IGNORECASE):
            relevant_statements.append(text)

    return relevant_statements

def fetch_and_process_page(link, politician_name):
    """Fetches a web page and extracts relevant political statements."""
    try:
        page = requests.get(link, timeout=5)  # Set timeout to 5 sec per request
        relevant_statements = extract_relevant_statements(page.text, politician_name)
        
        if relevant_statements:
            return {"source": link, "content": relevant_statements}
    except Exception as e:
        print(f"Skipping {link}: {e}")
        return None

def scrape_promises_via_api(politician_name, country="USA"):
    """Fetches relevant political statements for a given politician using Google Search API."""
    search_query = f"{politician_name} campaign promises site:.gov OR site:.news OR site:.edu OR site:.org"
    results = google_search(search_query)

    links = [item["link"] for item in results]
    print(f"Found {len(links)} sources for {politician_name}")

    promises = []

    # Use ThreadPoolExecutor to speed up fetching & processing
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(lambda link: fetch_and_process_page(link, politician_name), links[:15])

    # Filter out None results
    for result in results:
        if result:
            promises.append(result)

    return promises

# Test with a politician
politician = "Narendra Modi"
start_time = time.time()
promises = scrape_promises_via_api(politician, "India")
end_time = time.time()

# Save results
with open(f"{politician}_promises.json", "w") as f:
    json.dump(promises, f, indent=4)

print(f"Saved {len(promises)} political statements for {politician} in {round(end_time - start_time, 2)} seconds")
