from typing import List


class TextChunker:
    def __init__(self, max_tokens: int = 400):
        self.max_tokens = max_tokens

    def _token_count(self, text: str) -> int:
        return max(1, len(text) // 4)

    def _find_split_point(
        self,
        text: str,
        mid: int
    ) -> int:

        sentence_endings = [". ", "! ", "? "]

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

            candidates = []

            if left != -1:
                candidates.append(
                    left + len(ending)
                )

            if right != -1:
                candidates.append(
                    right + len(ending)
                )

            for pos in candidates:
                distance = abs(mid - pos)

                if distance < best_distance:
                    best_distance = distance
                    best_pos = pos

        if best_pos is not None:
            return best_pos

        return mid

    def _split_large_paragraph(
        self,
        text: str
    ) -> List[str]:

        if self._token_count(text) <= self.max_tokens:
            return [text]

        mid = len(text) // 2

        split_point = self._find_split_point(
            text,
            mid
        )

        left = text[:split_point].strip()
        right = text[split_point:].strip()

        chunks = []

        if left:
            chunks.extend(
                self._split_large_paragraph(left)
            )

        if right:
            chunks.extend(
                self._split_large_paragraph(right)
            )

        return chunks

    def _chunk_text(
        self,
        text: str
    ) -> List[str]:

        paragraphs = [
            p.strip()
            for p in text.split("\n\n")
            if p.strip()
        ]

        chunks = []

        current_chunk = []
        current_tokens = 0

        for paragraph in paragraphs:

            paragraph_tokens = self._token_count(
                paragraph
            )

            if paragraph_tokens > self.max_tokens:

                if current_chunk:
                    chunks.append(
                        "\n\n".join(current_chunk)
                    )

                    current_chunk = []
                    current_tokens = 0

                chunks.extend(
                    self._split_large_paragraph(
                        paragraph
                    )
                )

                continue

            if (
                current_tokens +
                paragraph_tokens
                <= self.max_tokens
            ):
                current_chunk.append(paragraph)
                current_tokens += paragraph_tokens

            else:
                chunks.append(
                    "\n\n".join(current_chunk)
                )

                current_chunk = [paragraph]
                current_tokens = paragraph_tokens

        if current_chunk:
            chunks.append(
                "\n\n".join(current_chunk)
            )

        return chunks

    def chunk_sections(
        self,
        sections: List[dict]
    ) -> List[dict]:

        chunks = []

        for section in sections:

            text_chunks = self._chunk_text(
                section["content"]
            )

            for idx, chunk in enumerate(text_chunks):

                chunks.append(
                    {
                        "chunk_id":
                            f"{section['section_id']}_chunk_{idx:03d}",

                        "section_id":
                            section["section_id"],

                        "section_name":
                            section["section_name"],

                        "section_order":
                            section["section_order"],

                        "chunk_index":
                            idx,

                        "start_page":
                            section["start_page"],

                        "end_page":
                            section["end_page"],

                        "content":
                            chunk,

                        "token_count":
                            self._token_count(chunk)
                    }
                )

        return chunks