from typing import List


class TextChunker:
    def __init__(self, max_tokens: int = 400):
        self.max_tokens = max_tokens
    
    def _token_count(self, text: str):
        return max(1, len(text) // 4)
    
    def _find_split_point(self, text: str, mid: int) -> int:
        sentence_endings = [". ", "! ", "? "]

        best_pos = None
        best_distance = float("inf")

        for ending in sentence_endings:
            left = text.rfind(ending, 0, mid)
            right = text.find(ending, mid)

            candidates = []

            if left != -1:
                candidates.append(left + len(ending))

            if right != -1:
                candidates.append(right + len(ending))

            for pos in candidates:
                distance = abs(mid - pos)

                if distance < best_distance:
                    best_distance = distance
                    best_pos = pos

        if best_pos is not None:
            return best_pos

        # paragraph boundary
        left = text.rfind("\n\n", 0, mid)
        right = text.find("\n\n", mid)

        candidates = [p for p in (left, right) if p != -1]

        if candidates:
            return min(candidates, key=lambda p: abs(mid - p))

        # whitespace boundary
        left = text.rfind(" ", 0, mid)
        right = text.find(" ", mid)

        candidates = [p for p in (left, right) if p != -1]

        if candidates:
            return min(candidates, key=lambda p: abs(mid - p))

        return mid
    
    def _chunk_text(self, text: str) -> List[str]:
        if self._token_count(text) <= self.max_tokens:
            return [text]

        mid = len(text) // 2

        split_point = self._find_split_point(text, mid)

        left = text[:split_point].strip()
        right = text[split_point:].strip()

        chunks = []

        if left:
            chunks.extend(self._chunk_text(left))

        if right:
            chunks.extend(self._chunk_text(right))

        return chunks
    
    def chunk_sections(self, sections: List[dict]) -> List[dict]:
        chunks = []

        for section in sections:
            section_name = section["header"]
            section_text = section["content"]

            text_chunks = self._chunk_text(section_text)

            for idx, chunk in enumerate(text_chunks):
                chunks.append(
                    {
                        "section": section_name,
                        "chunk_index": idx,
                        "content": chunk,
                        "token_count": self._token_count(chunk)
                    }
                )

        return chunks
