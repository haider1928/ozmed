from ddgs import DDGS
import time
import requests
from bs4 import BeautifulSoup

def extract_page_text(url: str, max_chars: int = 8000):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove useless tags
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
            tag.decompose()

        # Extract visible text
        text = soup.get_text(separator="\n")

        # Clean whitespace
        lines = [line.strip() for line in text.splitlines()]
        clean_text = "\n".join(line for line in lines if line)

        # Limit size (important for LLM use)
        return clean_text[:max_chars]

    except Exception as e:
        return f"ERROR: {str(e)}"
    

def search_internet(action_json):
    outputs = []

    queries = action_json["search_internet"].get("queries", [])
    max_results = action_json["search_internet"].get("results", 3)

    

    with DDGS() as ddgs:
        for query in queries:
            results = []

            try:
                # slight delay helps avoid silent blocking
                time.sleep(0.5)

                raw_results = list(ddgs.text(query, max_results=max_results))

                # fallback if empty
                if not raw_results:
                    outputs.append({
                        "query": query,
                        "results": [],
                        "warning": "No results returned (possible DDGS block or weak query)"
                    })
                    continue

                for r in raw_results:
                    results.append({
                        "title": r.get("title", "No title"),
                        "link": r.get("href", "No link")
                    })

                outputs.append({
                    "query": query,
                    "results": results
                })

            except Exception as e:
                outputs.append({
                    "query": query,
                    "error": str(e)
                })

    return outputs

def search_urls(ddgs_results):
    outputs = []
    for search in ddgs_results:
        results = search.get("results", [])
        query = search.get("query", "No query")
        urls = list(r.get("link", "No link") for r in results) if results else ["No results"]
        for url in urls:
            text = extract_page_text(url)
            outputs.append({
                
                "query": query,
                "url": url,
                "text": text
            })
    return outputs



if __name__ == "__main__":
    test_json = {
        "search_internet": {
            "queries": ["latest AI news", "Python programming"],
            "results": 2
        }
    }
    #{"search_internet":{"queries":["Khwaja Mohsin Inam PGC"],"results":4}}

    search_results = search_internet(test_json)
    print(search_urls(search_results))