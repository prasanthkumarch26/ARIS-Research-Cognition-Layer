import asyncio
import re
import unicodedata

from collections import defaultdict
from typing import Optional

import fitz
import httpx

from app.services.chunker import TextChunker
from app.models.paper_models import Section, SectionType, ParsedPaper


HEADER_RE = re.compile(
    r"^[A-Z0-9][A-Za-z0-9.\-\s]*$"
)

NO_SECTION_HEADERS = {
    "table",
    "figure",
    "algorithm",
    "lemma",
    "theorem",
    "definition",
    "corollary",
}

NOISE_PATTERNS = [
    re.compile(r"^arXiv:", re.IGNORECASE),
    re.compile(r"^Copyright", re.IGNORECASE),
    re.compile(r"^\*\s*Equal contribution\.?$", re.IGNORECASE),
    re.compile(r"^†\s*Corresponding author\.?$", re.IGNORECASE),
    re.compile(r"^\d+$"),
]

REFERENCE_SECTION_PATTERNS = [
    re.compile(r"^references?$", re.IGNORECASE),
    re.compile(r"^bibliography$", re.IGNORECASE),
    re.compile(r"^works cited$", re.IGNORECASE),
    re.compile(r"^citations?$", re.IGNORECASE),
    re.compile(r"^reference list$", re.IGNORECASE),
    re.compile(r"^literature cited$", re.IGNORECASE),
]





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
    
    def _normalize_section_name(self, section_name: str) -> str:
        return re.sub(
            r"^\d+(\.\d+)*\.?\s+", "", section_name.strip()
            )
    
    def _get_section_type(self, section_name: str) -> SectionType:
        normalized = self._normalize_section_name(section_name)

        if any(
            pattern.fullmatch(normalized)
            for pattern in REFERENCE_SECTION_PATTERNS
        ):
            return SectionType.REFERENCES

        return SectionType.CONTENT

    def _parse_document(self, doc: fitz.Document) -> ParsedPaper:
        body_font_size = self._detect_body_font_size(doc)

        sections = self._extract_sections(
            doc,
            body_font_size + 1 if body_font_size else None
        )

        return ParsedPaper(
            page_count=doc.page_count,
            body_font_size=body_font_size,
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

    def _is_noise_line(self, text: str) -> bool:
        text = text.strip()

        return any(
            pattern.match(text)
            for pattern in NOISE_PATTERNS
        )

    def _is_excluded_header(self, text: str) -> bool:
        text = text.strip().lower()

        return any(
            text.startswith(f"{prefix} ")
            for prefix in NO_SECTION_HEADERS
        )

    def _extract_sections(self, doc: fitz.Document, header_size_threshold: Optional[float]) -> list[Section]:

        if header_size_threshold is None:
            return []

        sections: list[Section] = []
        section_counter: int = 0
        abstract_found: bool = False
        current_section: Optional[dict] = None
        content_buffer: list[str] = []

        

        for page_num, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")

            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue

                for line in block.get("lines", []):

                    spans = [
                        span
                        for span in line.get("spans", [])
                        if span["text"].strip()
                    ]

                    if not spans:
                        continue

                    line_text = " ".join(
                        span["text"].strip()
                        for span in spans
                    )

                    if self._is_noise_line(line_text):
                        continue

                    # if self._is_excluded_header(line_text):
                    #     continue

                    first_span = spans[0]

                    if line_text.strip().lower().rstrip(":") == "abstract":
                        abstract_found = True
                        continue

                    if not abstract_found:
                        continue

                    is_header = (
                        first_span["size"] > header_size_threshold
                        and HEADER_RE.match(line_text)
                        and not self._is_excluded_header(line_text)
                    )

                    if is_header:
                        if current_section is None:
                            section_counter = 0

                            current_section = {
                                "section_id": f"sec_{section_counter:03d}",
                                "section_order": section_counter,
                                "section_name": line_text,
                                "start_page": page_num,
                                "end_page": None,
                                "last_content_page": None,
                            }

                            continue

                        if content_buffer:

                            current_section["end_page"] = (
                                current_section["last_content_page"]
                                or current_section["start_page"]
                                or page_num
                            )

                            section_data = {
                                k: v
                                for k, v in current_section.items()
                                if k != "last_content_page"
                            }

                            sections.append(
                                Section(
                                    **section_data,
                                    section_type=self._get_section_type(
                                        current_section["section_name"]
                                    ),
                                    content=self._clean_text(
                                        "\n\n".join(content_buffer)
                                    )
                                )
                            )

                        section_counter += 1

                        current_section = {
                            "section_id": f"sec_{section_counter:03d}",
                            "section_order": section_counter,
                            "section_name": line_text,
                            "start_page": page_num,
                            "end_page": None,
                            "last_content_page": None,
                        }

                        content_buffer = []

                    else:
                        if current_section is None:
                            continue

                        content_buffer.append(line_text)
                        current_section["last_content_page"] = page_num

        if content_buffer:

            current_section["end_page"] = (
                current_section["last_content_page"]
                or current_section["start_page"]
                or doc.page_count
            )

            section_data = {
                k: v
                for k, v in current_section.items()
                if k != "last_content_page"
            }

            sections.append(
                Section(
                    **section_data,
                    section_type=self._get_section_type(
                        current_section["section_name"]
                    ),
                    content=self._clean_text(
                        "\n\n".join(content_buffer)
                    )
                )
            )

        return sections

    def _clean_text(self, text: str) -> str:
        text = unicodedata.normalize("NFKD", text)
        text = re.sub(r'-\s+', '', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()


async def main():
    parser = PaperParser()

    paper = await parser.parse_from_url(
        "https://arxiv.org/pdf/2112.09300v1"
    )

    for section in paper.sections:
        print(
            section.section_order,
            section.section_name,
            section.section_type,
            section.start_page,
            section.end_page
        )
    chunker = TextChunker(max_tokens=400)
    
    chunks = chunker.chunk_sections(
        paper.sections
    )
    
    for chunk in chunks[:5]:
        print(chunk)
        print("-" * 100)


if __name__ == "__main__":
    asyncio.run(main())