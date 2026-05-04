"""feedback_loop.py - Sistema de aprendizaje por feedback"""
import sqlite3, os
from datetime import datetime

class FeedbackLoop:
    def __init__(self, db_path='tpv_datos.db'):
        self.db_path = db_path
        self._init_db()
    
    def _get_conn(self):
        for path in [self.db_path, os.path.join(os.path.dirname(__file__), '..', self.db_path)]:
            if os.path.exists(path):
                return sqlite3.connect(path)
        return None
    
    def _init_db(self):
        conn = self._get_conn()
        if not conn:
            return
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pregunta TEXT NOT NULL,
                    respuesta TEXT,
                    intent_detectado TEXT,
                    rating INTEGER CHECK(rating IN (0,1)),
                    usuario TEXT,
                    fecha TEXT DEFAULT (datetime('now','localtime'))
                )
            ''')
            conn.commit()
        except:
            pass
        finally:
            conn.close()
    
    def save_feedback(self, question, response, intent, rating, user='anon'):
        """Guarda feedback del usuario (1=positivo, 0=negativo)"""
        conn = self._get_conn()
        if not conn:
            return
        try:
            conn.execute(
                "INSERT INTO ai_feedback (pregunta, respuesta, intent_detectado, rating, usuario) VALUES (?,?,?,?,?)",
                (question[:500], response[:500], intent, rating, user)
            )
            conn.commit()
        except:
            pass
        finally:
            conn.close()
    
    def get_low_rated(self, limit=10):
        """Obtiene preguntas mal calificadas para mejorar"""
        conn = self._get_conn()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT pregunta, intent_detectado, COUNT(*) c FROM ai_feedback WHERE rating=0 GROUP BY intent_detectado ORDER BY c DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [{'intent': r[1], 'count': r[2], 'example': r[0]} for r in rows]
        except:
            return []
        finally:
            conn.close()
