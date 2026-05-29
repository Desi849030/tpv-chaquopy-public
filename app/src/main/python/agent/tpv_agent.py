import os
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
from dataclasses import dataclass, asdict

@dataclass
class TPVAgent:
    agent_id: str
    device_id: str
    status: str = "offline"
    last_sync: datetime = None
    pending_actions: List[Dict] = None
    
    def __post_init__(self):
        self.pending_actions = self.pending_actions or []
        self.last_sync = self.last_sync or datetime.now()

class OfflineFirstAgentManager:
    def __init__(self, db_path="agents.db"):
        self.agents: Dict[str, TPVAgent] = {}
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
        self._load_agents()
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                device_id TEXT,
                status TEXT,
                last_sync TEXT,
                pending_actions TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                action_type TEXT,
                data TEXT,
                timestamp TEXT,
                synced INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_agents(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM agents")
        rows = cursor.fetchall()
        
        for row in rows:
            agent = TPVAgent(
                agent_id=row[0],
                device_id=row[1],
                status=row[2],
                last_sync=datetime.fromisoformat(row[3]),
                pending_actions=json.loads(row[4]) if row[4] else []
            )
            self.agents[agent.agent_id] = agent
        
        conn.close()
    
    def register_agent(self, agent_id: str, device_id: str) -> TPVAgent:
        with self.lock:
            if agent_id not in self.agents:
                agent = TPVAgent(agent_id=agent_id, device_id=device_id)
                self.agents[agent_id] = agent
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO agents VALUES (?, ?, ?, ?, ?)
                ''', (agent_id, device_id, agent.status, 
                      agent.last_sync.isoformat(), 
                      json.dumps(agent.pending_actions)))
                conn.commit()
                conn.close()
            
            return self.agents[agent_id]
    
    def add_pending_action(self, agent_id: str, action: Dict):
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id].pending_actions.append({
                    **action,
                    'timestamp': datetime.now().isoformat()
                })
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sync_queue (agent_id, action_type, data, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (agent_id, action.get('type'), 
                      json.dumps(action), datetime.now().isoformat()))
                conn.commit()
                conn.close()
    
    def get_pending_actions(self, agent_id: str) -> List[Dict]:
        return self.agents.get(agent_id, {}).pending_actions or []
    
    def sync_agent(self, agent_id: str) -> Dict:
        with self.lock:
            if agent_id not in self.agents:
                return {'status': 'error', 'message': 'Agent not found'}
            
            agent = self.agents[agent_id]
            agent.last_sync = datetime.now()
            agent.status = 'online'
            
            pending = agent.pending_actions.copy()
            agent.pending_actions = []
            
            return {
                'status': 'success',
                'agent_id': agent_id,
                'synced_actions': len(pending),
                'pending_data': pending,
                'timestamp': agent.last_sync.isoformat()
            }
