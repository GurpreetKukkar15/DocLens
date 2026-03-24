import requests
import os
import time
import xml.etree.ElementTree as ET

SEARCH_QUERY = "retrieval augmented generation"
MAX_PAPERS = 75
OUTPUT_DIR = os.path.expanduser("~/Desktop/doclens/backend/data/papers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def search_arxiv(query, max_results=75):
    """Search ArXiv for papers matching query"""
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    response = requests.get(url, params=params)
    return response.text

def parse_arxiv_results(xml_text):
    """Parse ArXiv API response and extract paper IDs and titles"""
    root = ET.fromstring(xml_text)
    namespace = "{http://www.w3.org/2005/Atom}"
    
    papers = []
    for entry in root.findall(f"{namespace}entry"):
        arxiv_id = entry.find(f"{namespace}id").text
        title = entry.find(f"{namespace}title").text.strip()
        
        # Extract just the ID from the URL
        paper_id = arxiv_id.split("/abs/")[-1]
        
        papers.append({
            "id": paper_id,
            "title": title
        })
    
    return papers

def download_pdf(paper_id, title, index):
    """Download a single PDF from ArXiv"""
    pdf_url = f"https://arxiv.org/pdf/{paper_id}"
    
    # Clean filename
    clean_title = "".join(c for c in title if c.isalnum() or c in " -_")[:60]
    filename = f"{index:03d}_{clean_title}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"Already exists: {filename}")
        return True
    
    try:
        response = requests.get(pdf_url, timeout=30)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"Downloaded {index}/{MAX_PAPERS}: {filename}")
            return True
        else:
            print(f"Failed {index}: {title} (status {response.status_code})")
            return False
    except Exception as e:
        print(f"Error {index}: {title} — {e}")
        return False

def main():
    print(f"Searching ArXiv for: '{SEARCH_QUERY}'")
    xml_text = search_arxiv(SEARCH_QUERY, MAX_PAPERS)
    papers = parse_arxiv_results(xml_text)
    print(f"Found {len(papers)} papers")
    print(f"Downloading PDFs to: {OUTPUT_DIR}\n")
    
    downloaded = 0
    for i, paper in enumerate(papers, start=1):
        success = download_pdf(paper["id"], paper["title"], i)
        if success:
            downloaded += 1
        # Be polite to ArXiv — wait between downloads
        time.sleep(2)
    
    print(f"\nDone! Downloaded {downloaded}/{len(papers)} papers")
    print(f"Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()