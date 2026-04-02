import os
import lancedb
from lancedb.pydantic import Vector, LanceModel
import logging
from config import settings
from typing import List

from lancedb.rerankers import RRFReranker
from typing import List, Optional

logger = logging.getLogger("VectorStore")

class ContextDocument(LanceModel):
    uri: str
    text: str
    abstract: str = ""
    vector: Vector(768)
    metadata: str = "{}"

class VectorStore:
    def __init__(self):
        os.makedirs(settings.GCE_DB_PATH, exist_ok=True)
        self.db = lancedb.connect(settings.GCE_DB_PATH)
        self.table_name = "context_store"
        
        if self.table_name not in self.db.table_names():
            self.table = self.db.create_table(self.table_name, schema=ContextDocument)
            logger.info(f"Created new LanceDB table: {self.table_name}")
        else:
            self.table = self.db.open_table(self.table_name)
            logger.info(f"Opened LanceDB table: {self.table_name}")
        
        # Inicjalizacja rerankera RRF (Reciprocal Rank Fusion)
        self.reranker = RRFReranker()
        
        # Optymalizacja: Tworzenie indeksów FTS tylko jeśli tabela ma dane i indeksy nie istnieją (lub replace=False)
        if self.table.count_rows() > 0:
            try:
                # LanceDB v0.17+ automatycznie zarządza indeksami, ale dla pewności 
                # sprawdzamy czy wyszukiwanie FTS działa zamiast wymuszać replace=True
                logger.info("FTS check...")
                # Próba wyszukiwania testowego
                self.table.search("test", query_type="fts").limit(1).to_list()
            except Exception:
                logger.info("Creating FTS indexes on 'text' and 'abstract' columns...")
                self.table.create_fts_index("text", replace=True)
                self.table.create_fts_index("abstract", replace=True)

    def get_stats(self) -> dict:
        """Pobiera rozszerzone statystyki bazy danych LanceDB."""
        total_chunks = self.table.count_rows()
        try:
            # Pobieramy wszystkie URI z tabeli
            results = self.table.search().to_list()
            all_uris_full = [res['uri'] for res in results]
            
            # Unikalne zasoby (bez fragmentów)
            base_uris = [u.split('#')[0] for u in all_uris_full]
            unique_resources = len(set(base_uris))
            
            # Liczba wspomnień (memories)
            memories_count = len([u for u in set(base_uris) if u.startswith("gce://user/memories/")])
            
            # Top 5 największych zasobów
            from collections import Counter
            counts = Counter(base_uris)
            top_resources = [{"uri": uri, "chunks": count} for uri, count in counts.most_common(5)]
            
            # Rozmiar na dysku
            import subprocess
            try:
                du_output = subprocess.check_output(['du', '-sh', settings.GCE_DB_PATH]).decode('utf-8')
                db_size = du_output.split()[0]
            except:
                db_size = "unknown"
                
        except Exception as e:
            logger.error(f"Stats error: {e}")
            unique_resources = 0
            memories_count = 0
            top_resources = []
            db_size = "error"

        return {
            "total_chunks": total_chunks,
            "unique_resources": unique_resources,
            "memories_count": memories_count,
            "db_path": settings.GCE_DB_PATH,
            "db_size": db_size,
            "top_resources": top_resources
        }

    def add_documents(self, documents: List[dict]):
        """Dodaje listę fragmentów dokumentów do bazy."""
        if not documents:
            return
            
        base_uri = documents[0]['uri'].split('#')[0]
        try:
            # Usuwamy stare fragmenty dla tego samego zasobu, aby uniknąć duplikatów
            self.table.delete(f"uri LIKE '{base_uri}%'")
        except Exception as e:
            logger.debug(f"No existing documents to delete for {base_uri}: {e}")
            
        self.table.add(documents)
        logger.info(f"Added/Updated {len(documents)} chunks for: {base_uri}")

    def update_metadata(self, uri: str, metadata_update: dict):
        """Aktualizuje metadane dla konkretnego URI (merge JSON)."""
        import json
        doc = self.get_by_uri(uri)
        if not doc:
            logger.error(f"Document not found for metadata update: {uri}")
            return False
            
        try:
            current_meta = json.loads(doc.get('metadata', '{}'))
            current_meta.update(metadata_update)
            new_meta_str = json.dumps(current_meta)
            
            # W LanceDB update wykonujemy przez delete + add (dla bezpieczeństwa spójności w tej wersji)
            # lub przez update() jeśli tabela to obsługuje.
            self.table.update(where=f"uri = '{uri}'", values={"metadata": new_meta_str})
            logger.info(f"Updated metadata for {uri}")
            return True
        except Exception as e:
            logger.error(f"Metadata update failed for {uri}: {e}")
            return False

    def hybrid_search(self, query: str, query_vector: List[float], limit: int = 5, where: Optional[str] = None) -> List[dict]:
        """
        Wyszukiwanie hybrydowe z opcjonalnym rozszerzeniem o relacje.
        """
        import json
        try:
            search_builder = self.table.search(query_type="hybrid") \
                .vector(query_vector) \
                .text(query) \
                .rerank(self.reranker) \
                .limit(limit)
            
            if where:
                search_builder = search_builder.where(where)
                
            results = search_builder.to_list()
            
            # GCE 2.0: Automatyczne dociąganie powiązanych faktów (Simple Graph Traversal)
            enhanced_results = []
            seen_uris = {res['uri'] for res in results}
            
            for res in results:
                enhanced_results.append(res)
                # Sprawdzamy czy są relacje typu "see_also" lub "depends_on"
                try:
                    meta = json.loads(res.get('metadata', '{}'))
                    relations = meta.get('relations', [])
                    for rel in relations:
                        related_uri = rel.get('object_uri')
                        if related_uri and related_uri not in seen_uris:
                            related_doc = self.get_by_uri(related_uri)
                            if related_doc:
                                related_doc['_source'] = 'graph_relation'
                                enhanced_results.append(related_doc)
                                seen_uris.add(related_uri)
                except:
                    continue
                
            return enhanced_results[:limit + 2] # Pozwalamy na lekkie przekroczenie limitu dla relacji
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return self.table.search(query_vector).limit(limit).to_list()


    def get_by_uri(self, uri: str) -> dict:
        """Pobiera pojedynczy dokument po jego unikalnym URI."""
        results = self.table.search().where(f"uri = '{uri}'").to_list()
        return results[0] if results else None

vector_store = VectorStore()
