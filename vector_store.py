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
    namespace: str = "default"

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
            # GCE 2.5 Migration: Ensure namespace column exists (dynamic in LanceDB)
        
        # Inicjalizacja rerankera RRF (Reciprocal Rank Fusion)
        self.reranker = RRFReranker()
        
        # Optymalizacja: Tworzenie indeksów FTS
        if self.table.count_rows() > 0:
            try:
                self.table.search("test", query_type="fts").limit(1).to_list()
            except Exception:
                logger.info("Creating FTS indexes on 'text' and 'abstract' columns...")
                self.table.create_fts_index("text", replace=True)
                self.table.create_fts_index("abstract", replace=True)

    def get_stats(self) -> dict:
        """Pobiera rozszerzone statystyki bazy danych LanceDB."""
        total_chunks = self.table.count_rows()
        try:
            results = self.table.search().to_list()
            all_uris_full = [res['uri'] for res in results]
            namespaces = list(set([res.get('namespace', 'default') for res in results]))
            
            base_uris = [u.split('#')[0] for u in all_uris_full]
            unique_resources = len(set(base_uris))
            memories_count = len([u for u in set(base_uris) if u.startswith("gce://user/memories/")])
            
            from collections import Counter
            counts = Counter(base_uris)
            top_resources = [{"uri": uri, "chunks": count} for uri, count in counts.most_common(5)]
            
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
            namespaces = ["default"]

        return {
            "total_chunks": total_chunks,
            "unique_resources": unique_resources,
            "memories_count": memories_count,
            "db_path": settings.GCE_DB_PATH,
            "db_size": db_size,
            "top_resources": top_resources,
            "namespaces": namespaces
        }

    def add_documents(self, documents: List[dict]):
        """Dodaje listę fragmentów dokumentów do bazy (obsługa namespace)."""
        if not documents:
            return
            
        base_uri = documents[0]['uri'].split('#')[0]
        # Ustawiamy domyślny namespace jeśli brak
        for doc in documents:
            if 'namespace' not in doc:
                doc['namespace'] = 'default'

        try:
            self.table.delete(f"uri LIKE '{base_uri}%'")
        except Exception as e:
            logger.debug(f"No existing documents to delete for {base_uri}: {e}")
            
        self.table.add(documents)
        logger.info(f"Added/Updated {len(documents)} chunks for: {base_uri} in namespace {documents[0]['namespace']}")

    def hybrid_search(self, query: str, query_vector: List[float], limit: int = 5, where: Optional[str] = None, namespace: Optional[str] = None) -> List[dict]:
        """
        Wyszukiwanie hybrydowe z opcjonalnym filtrowaniem po namespace.
        """
        import json
        try:
            # Budowanie warunku WHERE dla namespace
            ns_filter = f"namespace = '{namespace}'" if namespace else None
            
            if where and ns_filter:
                final_where = f"({where}) AND ({ns_filter})"
            else:
                final_where = where or ns_filter

            search_builder = self.table.search(query_type="hybrid") \
                .vector(query_vector) \
                .text(query) \
                .rerank(self.reranker) \
                .limit(limit)
            
            if final_where:
                search_builder = search_builder.where(final_where)
                
            results = search_builder.to_list()
            
            enhanced_results = []
            seen_uris = {res['uri'] for res in results}
            
            for res in results:
                enhanced_results.append(res)
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
                
            return enhanced_results[:limit + 2]
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback bez hybrydy jeśli coś pójdzie nie tak (np. brak indeksu FTS)
            return self.table.search(query_vector).limit(limit).to_list()


    def get_by_uri(self, uri: str) -> dict:
        """Pobiera pojedynczy dokument po jego unikalnym URI."""
        results = self.table.search().where(f"uri = '{uri}'").to_list()
        return results[0] if results else None

vector_store = VectorStore()
