from dataclasses import dataclass
from typing import Optional
from enum import StrEnum


class SectionType(StrEnum):
    CONTENT = "content"
    REFERENCES = "references"


@dataclass
class Section:
    section_id: str
    section_order: int
    section_name: str
    section_type: SectionType
    start_page: Optional[int]
    end_page: Optional[int]
    content: str


@dataclass
class ParsedPaper:
    page_count: int
    body_font_size: Optional[float]
    sections: list[Section]