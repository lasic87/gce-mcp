import logging
from typing import List

logger = logging.getLogger("TextUtils")

class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """
        Dzieli tekst rekurencyjnie używając listy separatorów.
        Gwarantuje, że fragmenty nie przekraczają chunk_size i mają określony overlap.
        """
        final_chunks = []
        
        # Start rekurencji
        self._recursive_split(text, self.separators, final_chunks)
        
        # Łączenie małych fragmentów w większe (do limitu chunk_size) z uwzględnieniem overlapu
        return self._merge_splits(final_chunks)

    def _recursive_split(self, text: str, separators: List[str], chunks: List[str]):
        if len(text) <= self.chunk_size:
            chunks.append(text)
            return

        # Wybór separatora
        separator = separators[-1]
        for s in separators:
            if s in text:
                separator = s
                break
        
        # Dzielenie po wybranym separatorze
        splits = text.split(separator)
        
        for i, s in enumerate(splits):
            # Dodajemy separator z powrotem (poza ostatnim elementem)
            if i < len(splits) - 1:
                s = s + separator
            
            if len(s) <= self.chunk_size:
                chunks.append(s)
            else:
                # Jeśli fragment nadal za duży, szukamy następnego separatora
                next_separators = separators[separators.index(separator) + 1:]
                if next_separators:
                    self._recursive_split(s, next_separators, chunks)
                else:
                    # Ostateczne cięcie na sztywno, jeśli brak separatorów
                    for j in range(0, len(s), self.chunk_size):
                        chunks.append(s[j:j + self.chunk_size])

    def _merge_splits(self, splits: List[str]) -> List[str]:
        merged = []
        current_chunk = ""
        
        for s in splits:
            if len(current_chunk) + len(s) <= self.chunk_size:
                current_chunk += s
            else:
                if current_chunk:
                    merged.append(current_chunk)
                
                # Przygotowanie nowego fragmentu z overlapem
                # Pobieramy końcówkę poprzedniego fragmentu
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                overlap_text = current_chunk[overlap_start:]
                
                current_chunk = overlap_text + s
                
                # Jeśli sam s jest za duży (nie powinno się zdarzyć po rekurencji)
                if len(current_chunk) > self.chunk_size:
                    merged.append(current_chunk[:self.chunk_size])
                    current_chunk = current_chunk[self.chunk_size:]

        if current_chunk:
            merged.append(current_chunk)
            
        return merged
