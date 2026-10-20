import os
import lancedb
from lancedb.pydantic import Vector, LanceModel
import logging
from config import settings
from typing import List, Optional
import json

from lancedb.rerankers import RRFReranker

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
        """Pobiera rozszerzone statystyki bazy danych LanceDB z optymalizacją wyboru kolumn."""
        total_chunks = self.table.count_rows()
        try:
            # Optymalizacja: pobieranie tylko uri i namespace zamiast pełnych obiektów
            results = self.table.search().select(["uri", "namespace"]).to_list()
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
            except Exception:
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

    def delete(self, uri: str):
        """Usuwa dokumenty o wskazanym URI lub rozpoczynające się od wskazanego URI (z bezpiecznym eskapowaniem cudzysłowów)."""
        try:
            escaped_uri = uri.replace("'", "''")
            self.table.delete(f"uri LIKE '{escaped_uri}%'")
            logger.info(f"Deleted chunks for URI pattern: {uri}")
        except Exception as e:
            logger.debug(f"No existing documents to delete for {uri}: {e}")

    def migrate_viking_to_gce(self) -> dict:
        """Migruje wszystkie zasoby ze schematu viking:// na gce://."""
        try:
            results = self.table.search().where("uri LIKE 'viking://%'").to_list()
            if not results:
                return {"migrated": 0, "status": "Brak rekordów viking://"}

            migrated_docs = []
            for r in results:
                new_doc = dict(r)
                new_doc['uri'] = r['uri'].replace("viking://", "gce://", 1)
                if new_doc['uri'].startswith("gce://user/memories/") and new_doc.get('namespace') == 'default':
                    new_doc['namespace'] = 'memories'
                migrated_docs.append(new_doc)

            self.table.delete("uri LIKE 'viking://%'")
            self.table.add(migrated_docs)
            logger.info(f"Migrated {len(migrated_docs)} records from viking:// to gce://")
            return {"migrated": len(migrated_docs), "status": "Sukces"}
        except Exception as e:
            logger.error(f"Migration error: {e}")
            return {"migrated": 0, "status": f"Błąd: {e}"}

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
            escaped_base_uri = base_uri.replace("'", "''")
            self.table.delete(f"uri LIKE '{escaped_base_uri}%'")
        except Exception as e:
            logger.debug(f"No existing documents to delete for {base_uri}: {e}")
            
        self.table.add(documents)
        logger.info(f"Added/Updated {len(documents)} chunks for: {base_uri} in namespace {documents[0]['namespace']}")

    def hybrid_search(self, query: str, query_vector: List[float], limit: int = 5, where: Optional[str] = None, namespace: Optional[str] = None) -> List[dict]:
        """
        Wyszukiwanie hybrydowe z opcjonalnym filtrowaniem po namespace.
        """
        try:
            # Budowanie warunku WHERE dla namespace z bezpiecznym eskapowaniem
            if namespace:
                escaped_ns = namespace.replace("'", "''")
                ns_filter = f"namespace = '{escaped_ns}'"
            else:
                ns_filter = None
            
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
            
            enhanced_results = list(results)
            seen_uris = {res['uri'] for res in results}
            
            # Optymalizacja wsadowa: zbieramy wszystkie relacje grafowe i pobieramy jednym zapytaniem
            needed_uris = []
            for res in results:
                try:
                    meta = json.loads(res.get('metadata', '{}'))
                    for rel in meta.get('relations', []):
                        rel_uri = rel.get('object_uri')
                        if rel_uri and rel_uri not in seen_uris and rel_uri not in needed_uris:
                            needed_uris.append(rel_uri)
                except Exception:
                    continue

            if needed_uris:
                try:
                    escaped_uris = [u.replace("'", "''") for u in needed_uris[:10]]
                    rel_filter = " OR ".join(f"uri = '{u}'" for u in escaped_uris)
                    rel_docs = {d['uri']: d for d in self.table.search().where(rel_filter).to_list()}
                    for u in needed_uris:
                        if u in rel_docs:
                            doc = dict(rel_docs[u])
                            doc['_source'] = 'graph_relation'
                            enhanced_results.append(doc)
                            seen_uris.add(u)
                except Exception as e:
                    logger.debug(f"Batch relation lookup failed: {e}")
                
            return enhanced_results[:limit + 2]
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback bez hybrydy jeśli coś pójdzie nie tak (np. brak indeksu FTS)
            return self.table.search(query_vector).limit(limit).to_list()

    def get_by_uri(self, uri: str) -> dict:
        """Pobiera pojedynczy dokument po jego unikalnym URI z bezpiecznym eskapowaniem."""
        escaped_uri = uri.replace("'", "''")
        results = self.table.search().where(f"uri = '{escaped_uri}'").to_list()
        return results[0] if results else None

    def update_metadata(self, uri: str, metadata: dict):
        """Aktualizuje metadane dla zasobu o podanym URI z bezpiecznym eskapowaniem."""
        try:
            escaped_uri = uri.replace("'", "''")
            results = self.table.search().where(f"uri = '{escaped_uri}'").to_list()
            if results:
                doc = results[0]
                doc['metadata'] = json.dumps(metadata) if isinstance(metadata, dict) else metadata
                self.delete(uri)
                self.table.add([doc])
        except Exception as e:
            logger.error(f"Failed to update metadata for {uri}: {e}")

    def optimize(self):
        """Kompaktuje pliki tabeli i usuwa stare wersje w LanceDB w celu oszczędności miejsca i poprawy wydajności."""
        try:
            logger.info("Running LanceDB table optimization (compaction & cleanup)...")
            from datetime import timedelta
            self.table.optimize(cleanup_older_than=timedelta(hours=1), delete_unverified=True)
            logger.info("LanceDB table optimized successfully.")
        except Exception as e:
            logger.error(f"Failed to optimize LanceDB table: {e}")

vector_store = VectorStore()
