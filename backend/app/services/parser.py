import httpx
import fitz
import sys
import asyncio

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional

import unicodedata
import re

from chunker import TextChunker

@dataclass
class ParsedPaper:
    page_count: int
    max_size_counts: Optional[float]
    sections: List[dict]


class PaperParser:
    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout
    
    async def parse_from_url(self, pdf_url: str) -> ParsedPaper:
        pdf_bytes = await self._download_pdf(pdf_url)

        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            return self._parse_document(doc)

    async def _download_pdf(self, pdf_url: str) -> bytes:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()

            return response.content
    
    def _parse_document(self, doc: fitz.Document) -> ParsedPaper:
        max_size_counts = self._detect_body_font_size(doc)
        sections = self._extract_sections(doc, max_size_counts + 1)

        return ParsedPaper(
            page_count=doc.page_count,
            max_size_counts=max_size_counts,
            sections=sections,
        )

    def _detect_body_font_size(self, doc: fitz.Document) -> Optional[float]:
        size_counts = defaultdict(int)

        for page in doc:
            page_dict = page.get_text("dict")

            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue

                for line in block.get("lines", []):
                    for span in line.get("spans", []):

                        text = span["text"].strip()

                        if not text:
                            continue

                        font_size = round(span["size"], 1)

                        size_counts[font_size] += len(text)

        if not size_counts:
            return None

        return max(size_counts.items(), key=lambda x: x[1])[0]
    
    def _extract_sections(self, doc: fitz.Document, header_size_threshold: Optional[float]) -> List[dict]:
        if header_size_threshold is None:
            return []
        
        sections = []
        current_section = "Abstract"
        content_buffer = []
        abstract_found = False

        for page in doc:
            page_dict = page.get_text("dict")

            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue

                for line in block.get("lines", []):
                    for span in line.get("spans", []):

                        text = span["text"].strip()

                        if not text:
                            continue

                        if text.lower() == "abstract":
                            abstract_found = True

                        if not abstract_found:
                            continue

                        if span["size"] > header_size_threshold and text.istitle():
                            if content_buffer:
                                sections.append({
                                    "header": current_section,
                                    "content": self._clean_text(" ".join(content_buffer))
                                })
                
                            current_section = text
                            content_buffer = []
                        
                        else:
                            content_buffer.append(text)

        if content_buffer:
             sections.append({
                 "header": current_section,
                 "content": self._clean_text(" ".join(content_buffer))
             })
        return sections
    
    def _clean_text(self, text: str) -> str:
        text = unicodedata.normalize("NFKD", text)
        text = re.sub(r'-\s+', '', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()
    

async def main():
    parser = PaperParser()

    paper = await parser.parse_from_url("https://arxiv.org/pdf/2112.09300v1")

    chunker = TextChunker(max_tokens=400)

    chunks = chunker.chunk_sections(
        paper.sections
    )

    for chunk in chunks[:5]:
        print(chunk)
        print("-"*100)

if __name__ == "__main__":
    asyncio.run(main())
