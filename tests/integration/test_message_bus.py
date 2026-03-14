"""
Integration tests for message bus
"""
import pytest
import tempfile
import asyncio
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))


class TestMessageBusIntegration:
    """Test message bus operations"""
    
    @pytest.fixture
    def bus_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        # Initialize schema
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.executescript("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                sender TEXT,
                recipient TEXT,
                msg_type TEXT,
                status TEXT DEFAULT 'pending',
                payload TEXT,
                priority TEXT
            );
            CREATE TABLE agents (
                agent_id TEXT PRIMARY KEY,
                role TEXT,
                status TEXT
            );
        """)
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_message_persistence(self, bus_db):
        """Test that messages are persisted to database"""
        import sqlite3
        
        conn = sqlite3.connect(bus_db)
        conn.execute(
            "INSERT INTO messages (sender, recipient, msg_type, payload) VALUES (?, ?, ?, ?)",
            ("ceo", "cto", "directive", json.dumps({"task": "test"}))
        )
        conn.commit()
        
        cursor = conn.execute("SELECT * FROM messages WHERE sender = 'ceo'")
        result = cursor.fetchone()
        assert result is not None
        assert result[1] == "ceo"
        assert result[2] == "cto"
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
