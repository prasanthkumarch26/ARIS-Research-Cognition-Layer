import httpx
import asyncio
import xml.etree.ElementTree as ET
import time

_arxiv_lock = asyncio.Lock()
_last_request_time: float = 0.0

class ArxivClient:
    def __init__(self):
        headers = {
            "User-Agent": "PaperIntelligenceApp/1.0 (Learning Personal Project)"
        }
        self.client = httpx.AsyncClient(timeout=30, follow_redirects=True, headers=headers)
    
    def _parse_xml(self, xml_data : str):
        root = ET.fromstring(xml_data)
        entries = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            entry_dict = {
                "arxiv_id": entry.find("{http://www.w3.org/2005/Atom}id").text,
                "title": entry.find("{http://www.w3.org/2005/Atom}title").text,
                "abstract": entry.find("{http://www.w3.org/2005/Atom}summary").text,
                "authors": [author.find("{http://www.w3.org/2005/Atom}name").text for author in entry.findall("{http://www.w3.org/2005/Atom}author")],
                "arxiv_url": entry.find("{http://www.w3.org/2005/Atom}link").get("href"),
                "pdf_url": entry.find("{http://www.w3.org/2005/Atom}link").get("href").replace("abs", "pdf"),
                "published_date": entry.find("{http://www.w3.org/2005/Atom}published").text,
                "updated_date": entry.find("{http://www.w3.org/2005/Atom}updated").text,
            }
            entries.append(entry_dict)
        return entries
    
    async def search(self, query : str, max_results : int = 2):
        global _last_request_time
        
        async with _arxiv_lock:
            _last_request_time = time.monotonic()

            response = await self.client.get(f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}")
        if response.status_code != 200:
            print(f"Error: {response.status_code}: {response.text}")
            return []
        return self._parse_xml(response.text)
    
    async def close(self):
        await self.client.aclose()

async def main():
    client = ArxivClient()
    res = await client.search("transformers")
    print(res)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
