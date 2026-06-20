import logging
from typing import List, Optional
import tree_sitter_python as tspython
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser

logger = logging.getLogger("TextUtils")

class ASTCodeSplitter:
    """
    Inteligentny splitter kodu wykorzystujący Tree-sitter do wyodrębniania 
    znaczących jednostek logicznych (funkcje, klasy, metody).
    """
    def __init__(self, language: str, chunk_size: int = 2000):
        self.language_name = language.lower()
        self.chunk_size = chunk_size
        self.parser = Parser()
        
        try:
            if self.language_name == "python":
                self.language = Language(tspython.language())
            elif self.language_name in ["typescript", "ts", "tsx"]:
                self.language = Language(tstypescript.language_typescript())
            else:
                self.language = None
            
            if self.language:
                self.parser.language = self.language
        except Exception as e:
            logger.error(f"Błąd inicjalizacji Tree-sitter dla {language}: {e}")
            self.language = None

    def split_code(self, code: str) -> List[str]:
        """Dzieli kod na logiczne fragmenty (klasy/funkcje) przy użyciu AST."""
        if not self.language:
            return []

        # Tree-sitter operuje na bajtach, więc pracujemy na bajtach UTF-8
        code_bytes = bytes(code, "utf8")
        tree = self.parser.parse(code_bytes)
        root_node = tree.root_node
        
        chunks = []
        # Szukamy definicji klas i funkcji na najwyższym poziomie
        for child in root_node.children:
            if child.type in ["class_definition", "function_definition", "decorated_definition", "method_definition", "async_function_definition"]:
                chunk_text = code_bytes[child.start_byte:child.end_byte].decode("utf8", errors="ignore")
                
                # Jeśli funkcja jest za duża, dzielimy ją dalej (metody wewnątrz klasy)
                if len(chunk_text) > self.chunk_size and child.type == "class_definition":
                    chunks.extend(self._split_class(child, code_bytes))
                else:
                    chunks.append(chunk_text)
            elif child.type in ["import_from_statement", "import_statement", "lexical_declaration", "expression_statement"]:
                # Importy i stałe zbieramy jako jeden blok początkowy
                import_text = code_bytes[child.start_byte:child.end_byte].decode("utf8", errors="ignore")
                if not chunks:
                    chunks.append(import_text)
                else:
                    chunks[0] += "\n" + import_text
                    
        return [c for c in chunks if c.strip()]

    def _split_class(self, class_node, code_bytes: bytes) -> List[str]:
        """Dzieli klasę na mniejsze fragmenty (metody)."""
        class_header = ""
        methods = []
        for child in class_node.children:
            if child.type == "block":
                for block_child in child.children:
                    if block_child.type in ["function_definition", "method_definition", "decorated_definition", "async_function_definition"]:
                        methods.append(block_child)
            elif child.type == "identifier":
                class_name = code_bytes[child.start_byte:child.end_byte].decode("utf8", errors="ignore")
                class_header = f"class {class_name}:"

        chunks = []
        current_chunk = class_header + "\n"
        
        for method in methods:
            method_text = code_bytes[method.start_byte:method.end_byte].decode("utf8", errors="ignore")
            # Dodajemy kontekst klasy do każdej metody
            method_with_ctx = f"# Context: {class_header}\n{method_text}"
            
            if len(current_chunk) + len(method_with_ctx) <= self.chunk_size:
                current_chunk += "\n" + method_with_ctx
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = f"# Context: {class_header}\n{method_text}"
        
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n# ", "\n## ", "\n### ", "\n#### ",
            "\n```", "\n\n", "\n", ". ", "? ", "! ", ", ", " ", ""
        ]

    @classmethod
    def from_language(cls, language: str, chunk_size: int = 2000, chunk_overlap: int = 200):
        separators = {
            "python": ["\nclass ", "\ndef ", "\n\tdef ", "\n\n", "\n", " ", ""],
            "js": ["\nfunction ", "\nclass ", "\nconst ", "\n\n", "\n", " ", ""],
            "ts": ["\ninterface ", "\ntype ", "\nclass ", "\n\n", "\n", " ", ""],
            "markdown": ["\n# ", "\n## ", "\n### ", "\n\n", "\n", " ", ""]
        }.get(language.lower(), None)
        return cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=separators)

    def split_text(self, text: str, language: Optional[str] = None) -> List[str]:
        # GCE 3.0 Hybrid Strategy: AST first, then Recursive
        if language and language in ["python", "ts", "typescript"]:
            ast_splitter = ASTCodeSplitter(language, self.chunk_size)
            ast_chunks = ast_splitter.split_code(text)
            if ast_chunks:
                logger.info(f"Użyto AST Splitter dla {language} (wygenerowano {len(ast_chunks)} fragmentów)")
                return ast_chunks

        if not text: return []
        final_chunks = []
        self._recursive_split(text, self.separators, final_chunks)
        return self._merge_splits(final_chunks)

    def _recursive_split(self, text: str, separators: List[str], chunks: List[str]):
        if len(text) <= self.chunk_size:
            chunks.append(text)
            return
        selected_separator = separators[-1]
        for s in separators:
            if s in text:
                selected_separator = s
                break
        splits = text.split(selected_separator)
        current_text = ""
        for i, s in enumerate(splits):
            item = (selected_separator + s) if i > 0 else s
            if not item: continue
            if len(item) <= self.chunk_size:
                chunks.append(item)
            else:
                sep_idx = separators.index(selected_separator)
                next_separators = separators[sep_idx + 1:]
                if next_separators:
                    self._recursive_split(item, next_separators, chunks)
                else:
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
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                overlap_text = current_chunk[overlap_start:]
                current_chunk = overlap_text + s
        if current_chunk:
            merged.append(current_chunk)
        return merged
