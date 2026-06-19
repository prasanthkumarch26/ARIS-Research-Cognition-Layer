from typing import List
from app.models.paper_models import Section


class TextChunker:
    def __init__(
        self,
        max_tokens: int = 400,
        overlap_tokens: int = 50,
    ):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def _token_count(self, text: str) -> int:
        return max(1, len(text.split()))

    def _find_sentence_split(self, text: str) -> int:
        mid = len(text) // 2

        sentence_endings = [
            ". ",
            "! ",
            "? ",
            ".\n",
            "!\n",
            "?\n",
        ]

        best_pos = None
        best_distance = float("inf")

        for ending in sentence_endings:

            left = text.rfind(
                ending,
                0,
                mid
            )

            right = text.find(
                ending,
                mid
            )

            for pos in (left, right):

                if pos == -1:
                    continue

                split_pos = pos + len(ending)

                distance = abs(
                    split_pos - mid
                )

                if distance < best_distance:
                    best_distance = distance
                    best_pos = split_pos

        return best_pos or mid

    def _split_large_text(
        self,
        text: str
    ) -> List[str]:

        if self._token_count(text) <= self.max_tokens:
            return [text]

        split_point = self._find_sentence_split(text)

        left = text[:split_point].strip()
        right = text[split_point:].strip()

        chunks = []

        if left:
            chunks.extend(
                self._split_large_text(left)
            )

        if right:
            chunks.extend(
                self._split_large_text(right)
            )

        return chunks

    def _chunk_content(
        self,
        text: str
    ) -> List[str]:

        paragraphs = [
            p.strip()
            for p in text.split("\n\n")
            if p.strip()
        ]

        chunks = []
        current = []

        current_tokens = 0

        for paragraph in paragraphs:

            paragraph_tokens = self._token_count(
                paragraph
            )

            if paragraph_tokens > self.max_tokens:

                if current:
                    chunks.append(
                        "\n\n".join(current)
                    )

                    current = []
                    current_tokens = 0

                chunks.extend(
                    self._split_large_text(
                        paragraph
                    )
                )

                continue

            if (
                current_tokens +
                paragraph_tokens
                <= self.max_tokens
            ):
                current.append(paragraph)
                current_tokens += paragraph_tokens

            else:
                chunks.append(
                    "\n\n".join(current)
                )

                overlap = []

                overlap_tokens = 0

                for p in reversed(current):

                    p_tokens = self._token_count(p)

                    if (
                        overlap_tokens +
                        p_tokens
                        > self.overlap_tokens
                    ):
                        break

                    overlap.insert(0, p)
                    overlap_tokens += p_tokens

                current = overlap + [paragraph]

                current_tokens = (
                    overlap_tokens +
                    paragraph_tokens
                )

        if current:
            chunks.append(
                "\n\n".join(current)
            )

        return chunks

    def chunk_sections(
        self,
        sections: List[Section]
    ) -> List[dict]:

        chunks = []

        for section in sections:

            section_chunks = self._chunk_content(
                section.content
            )

            for idx, chunk in enumerate(section_chunks):

                chunks.append(
                    {
                        "chunk_id":
                            f"{section.section_id}_chunk_{idx:03d}",

                        "section_id":
                            section.section_id,

                        "section_name":
                            section.section_name,

                        "section_type":
                            section.section_type.value,

                        "section_order":
                            section.section_order,

                        "chunk_index":
                            idx,

                        "start_page":
                            section.start_page,

                        "end_page":
                            section.end_page,

                        "content":
                            chunk,

                        "token_count":
                            self._token_count(chunk),
                    }
                )

        return chunks