import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class KnowledgeGraph:
    def __init__(self, db_path: str = "/root/gce-mcp/data/knowledge_graph.sqlite3"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS triples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_to TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(subject)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_triples_object ON triples(object)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_triples_temporal ON triples(valid_from, valid_to)")
            conn.commit()

    def add_triple(self, subject: str, predicate: str, object: str, 
                   valid_from: Optional[str] = None, 
                   valid_to: Optional[str] = None, 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Dodaje fakt do grafu temporalnego."""
        if not valid_from:
            valid_from = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        meta_str = json.dumps(metadata or {})
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO triples (subject, predicate, object, valid_from, valid_to, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (subject.strip(), predicate.strip(), object.strip(), valid_from, valid_to, meta_str))
            conn.commit()
        return True

    def invalidate_triple(self, subject: str, predicate: str, object: str, 
                          ended: Optional[str] = None) -> int:
        """Oznacza fakt jako nieaktualny (ustawia valid_to)."""
        if not ended:
            ended = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE triples 
                SET valid_to = ? 
                WHERE subject = ? AND predicate = ? AND object = ? AND (valid_to IS NULL OR valid_to > ?)
            """, (ended, subject.strip(), predicate.strip(), object.strip(), ended))
            conn.commit()
            return cursor.rowcount

    def query_entity(self, entity: str, as_of: Optional[str] = None, direction: str = "both") -> List[Dict[str, Any]]:
        """Przeszukuje relacje powiązane z encją z uwzględnieniem temporalności."""
        entity = entity.strip()
        query = "SELECT id, subject, predicate, object, valid_from, valid_to, metadata FROM triples WHERE "
        params = []
        
        # Filtrowanie kierunku relacji
        if direction == "outgoing":
            query += "subject = ?"
            params.append(entity)
        elif direction == "incoming":
            query += "object = ?"
            params.append(entity)
        else: # both
            query += "(subject = ? OR object = ?)"
            params.extend([entity, entity])
            
        # Filtrowanie czasu (temporalność as_of)
        if as_of:
            query += " AND valid_from <= ? AND (valid_to IS NULL OR valid_to >= ?)"
            params.extend([as_of, as_of])
            
        results = []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "subject": row[1],
                    "predicate": row[2],
                    "object": row[3],
                    "valid_from": row[4],
                    "valid_to": row[5],
                    "metadata": json.loads(row[6])
                })
        return results

    def get_timeline(self, entity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Zwraca oś czasu faktów (chronologicznie)."""
        query = "SELECT id, subject, predicate, object, valid_from, valid_to, metadata FROM triples"
        params = []
        if entity:
            query += " WHERE subject = ? OR object = ?"
            params.extend([entity.strip(), entity.strip()])
        query += " ORDER BY valid_from ASC"
        
        results = []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "subject": row[1],
                    "predicate": row[2],
                    "object": row[3],
                    "valid_from": row[4],
                    "valid_to": row[5],
                    "metadata": json.loads(row[6])
                })
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Pobiera statystyki grafu wiedzy."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM triples")
            total_triples = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM triples WHERE valid_to IS NULL")
            active_triples = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT subject) FROM triples")
            unique_subjects = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT object) FROM triples")
            unique_objects = cursor.fetchone()[0]
            
        return {
            "total_facts": total_triples,
            "active_facts": active_triples,
            "expired_facts": total_triples - active_triples,
            "unique_entities": len(set([row for row in (unique_subjects, unique_objects)])) # Proste przybliżenie
        }

knowledge_graph = KnowledgeGraph()
