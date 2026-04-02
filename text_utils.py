import logging
from typing import List

logger = logging.getLogger("TextUtils")

class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Domyślne separatory zorientowane na Markdown i strukturę tekstu
        self.separators = separators or [
            "\n# ", "\n## ", "\n### ", "\n#### ",  # Nagłówki Markdown
            "\n```",                                # Bloki kodu
            "\n\n", "\n",                           # Akapity i linie
            ". ", "? ", "! ",                       # Koniec zdania
            ", ", " ", ""                           # Słowa i znaki
        ]

    @classmethod
    def from_language(cls, language: str, chunk_size: int = 2000, chunk_overlap: int = 200):
        """Tworzy splitter ze specyficznymi separatorami dla danego języka."""
        separators = {
            "python": [
                "\nclass ", "\ndef ", "\n\tdef ", "\n\t\tdef ",  # Klasy i funkcje
                "\n\n", "\n", "\n ", " ", ""                      # Struktura i spacje
            ],
            "js": [
                "\nfunction ", "\nclass ", "\nconst ", "\nlet ", "\nvar ",
                "\n\n", "\n", " ", ""
            ],
            "ts": [
                "\ninterface ", "\ntype ", "\nclass ", "\nfunction ", "\nconst ",
                "\n\n", "\n", " ", ""
            ],
            "markdown": [
                "\n# ", "\n## ", "\n### ", "\n#### ", "\n##### ", "\n###### ",
                "\n```", "\n\n", "\n", " ", ""
            ]
        }.get(language.lower(), None)
        
        return cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=separators)

    def split_text(self, text: str) -> List[str]:
        """
        Dzieli tekst rekurencyjnie używając listy separatorów.
        Gwarantuje, że fragmenty nie przekraczają chunk_size i mają określony overlap.
        """
        if not text:
            return []
            
        final_chunks = []
        self._recursive_split(text, self.separators, final_chunks)
        return self._merge_splits(final_chunks)

    def _recursive_split(self, text: str, separators: List[str], chunks: List[str]):
        if len(text) <= self.chunk_size:
            chunks.append(text)
            return

        # Wybór najlepszego separatora z dostępnych
        selected_separator = separators[-1]
        for s in separators:
            if s in text:
                selected_separator = s
                break
        
        # Dzielenie po wybranym separatorze
        # Jeśli separator to nagłówek, zachowujemy go na początku fragmentu (split z regex by był lepszy, ale użyjemy sprytnego join)
        splits = text.split(selected_separator)
        
        current_text = ""
        for i, s in enumerate(splits):
            # Przywracamy separator (chyba że to pierwszy element i split był na początku)
            if i > 0:
                item = selected_separator + s
            else:
                item = s
            
            if not item: continue

            if len(item) <= self.chunk_size:
                chunks.append(item)
            else:
                # Jeśli fragment nadal za duży, szukamy następnego separatora w hierarchii
                sep_idx = separators.index(selected_separator)
                next_separators = separators[sep_idx + 1:]
                if next_separators:
                    self._recursive_split(item, next_separators, chunks)
                else:
                    # Ostateczne cięcie na sztywno
                    for j in range(0, len(item), self.chunk_size):
                        chunks.append(item[j:j + self.chunk_size])

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
