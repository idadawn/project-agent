from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime
from workflow.state import ConversationSnapshot, WorkflowState


class SessionManager:
    def __init__(self, storage_dir: str = "./sessions"):
        self.storage_dir = storage_dir
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.snapshots: Dict[str, List[ConversationSnapshot]] = {}
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing sessions
        self._load_sessions()
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "created_at": self._get_timestamp(),
                "last_activity": self._get_timestamp(),
                "conversation_history": [],
                "metadata": {}
            }
            self._save_session(session_id)
        
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, data: Dict[str, Any]):
        if session_id not in self.sessions:
            self.sessions[session_id] = {}
        
        self.sessions[session_id].update(data)
        self.sessions[session_id]["last_activity"] = self._get_timestamp()
        self._save_session(session_id)
    
    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        # Delete snapshots
        if session_id in self.snapshots:
            del self.snapshots[session_id]
        
        # Delete session file
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(session_file):
            os.remove(session_file)
        
        # Delete snapshots file
        snapshots_file = os.path.join(self.storage_dir, f"{session_id}_snapshots.json")
        if os.path.exists(snapshots_file):
            os.remove(snapshots_file)
    
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        return self.sessions
    
    def create_snapshot(self, session_id: str, description: str) -> ConversationSnapshot:
        session_data = self.get_session(session_id)
        
        # Extract files content (remove legacy PROPOSAL_PLAN.md)
        files = {}
        if session_data.get("current_content"):
            files["投标文件.md"] = session_data["current_content"]
        
        snapshot = ConversationSnapshot(
            timestamp=self._get_timestamp(),
            state=session_data,
            files=files,
            description=description
        )
        
        if session_id not in self.snapshots:
            self.snapshots[session_id] = []
        
        self.snapshots[session_id].append(snapshot)
        self._save_snapshots(session_id)
        
        return snapshot
    
    def get_snapshots(self, session_id: str) -> List[ConversationSnapshot]:
        return self.snapshots.get(session_id, [])
    
    def restore_snapshot(self, session_id: str, snapshot_timestamp: str):
        snapshots = self.get_snapshots(session_id)
        
        for snapshot in snapshots:
            if snapshot.timestamp == snapshot_timestamp:
                self.sessions[session_id] = snapshot.state.copy()
                self._save_session(session_id)
                return
        
        raise ValueError(f"Snapshot not found: {snapshot_timestamp}")
    
    def _load_sessions(self):
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json") and not filename.endswith("_snapshots.json"):
                    session_id = filename[:-5]  # Remove .json extension
                    session_file = os.path.join(self.storage_dir, filename)
                    
                    with open(session_file, 'r', encoding='utf-8') as f:
                        self.sessions[session_id] = json.load(f)
                    
                    # Load snapshots
                    snapshots_file = os.path.join(self.storage_dir, f"{session_id}_snapshots.json")
                    if os.path.exists(snapshots_file):
                        with open(snapshots_file, 'r', encoding='utf-8') as f:
                            snapshots_data = json.load(f)
                            self.snapshots[session_id] = [
                                ConversationSnapshot(**snapshot) for snapshot in snapshots_data
                            ]
        except Exception as e:
            print(f"Error loading sessions: {e}")
    
    def _save_session(self, session_id: str):
        try:
            session_file = os.path.join(self.storage_dir, f"{session_id}.json")
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions[session_id], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
    
    def _save_snapshots(self, session_id: str):
        try:
            snapshots_file = os.path.join(self.storage_dir, f"{session_id}_snapshots.json")
            
            snapshots_data = [snapshot.dict() for snapshot in self.snapshots[session_id]]
            
            with open(snapshots_file, 'w', encoding='utf-8') as f:
                json.dump(snapshots_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving snapshots for session {session_id}: {e}")
    
    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager