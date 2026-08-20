"""Comprehensive tests for Memory and memory-integrated KaraEngine."""

from core.engine import KaraEngine
from core.memory import Memory
from core.router import Intent


class DummyAssistant:
    def send_message(self, text: str) -> str:
        return "dummy response"


# ============================================================================
# Memory Class Tests (Persistence and Error Handling)
# ============================================================================

def test_memory_persistence_across_instances(tmp_path) -> None:
    """Verify data persists across separate Memory instances."""
    path = str(tmp_path / "mem.json")
    
    # Create first instance and store data
    mem1 = Memory(path=path)
    mem1.set("name", "Alice")
    mem1.set("age", 30)
    
    # Create second instance and verify data is loaded
    mem2 = Memory(path=path)
    assert mem2.get("name") == "Alice"
    assert mem2.get("age") == 30


def test_memory_handles_missing_file(tmp_path) -> None:
    """Verify Memory gracefully handles missing JSON file."""
    path = str(tmp_path / "nonexistent" / "mem.json")
    mem = Memory(path=path)
    
    # Should start with empty data
    assert mem.all() == {}
    assert mem.get("key") is None
    
    # Should be able to save
    mem.set("key", "value")
    assert mem.get("key") == "value"


def test_memory_handles_empty_store(tmp_path) -> None:
    """Verify Memory works with empty initial store."""
    path = str(tmp_path / "mem.json")
    mem = Memory(path=path)
    
    # Empty memory
    assert len(mem.all()) == 0
    assert mem.get("missing_key") is None
    
    # Add and retrieve
    mem.set("key", "value")
    assert mem.get("key") == "value"


def test_memory_delete_existing_key(tmp_path) -> None:
    """Verify delete returns True and removes the key."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    mem.set("key", "value")
    
    assert mem.get("key") == "value"
    deleted = mem.delete("key")
    
    assert deleted is True
    assert mem.get("key") is None


def test_memory_delete_missing_key(tmp_path) -> None:
    """Verify delete returns False for missing key."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    
    deleted = mem.delete("nonexistent")
    
    assert deleted is False


def test_memory_clear(tmp_path) -> None:
    """Verify clear removes all data."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    mem.set("key1", "value1")
    mem.set("key2", "value2")
    
    assert len(mem.all()) == 2
    
    mem.clear()
    
    assert len(mem.all()) == 0
    assert mem.get("key1") is None


# ============================================================================
# KaraEngine Memory Integration Tests
# ============================================================================

def test_engine_accepts_memory_instance(tmp_path) -> None:
    """Verify engine correctly stores supplied Memory instance."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    assert engine.memory is mem


def test_engine_exposes_memory_property(tmp_path) -> None:
    """Verify engine.memory property is accessible and returns same instance."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    assert engine.memory is mem
    engine.memory.set("test_key", "test_value")
    assert mem.get("test_key") == "test_value"


def test_engine_with_no_memory(tmp_path) -> None:
    """Verify engine works gracefully when memory=None."""
    engine = KaraEngine(assistant=DummyAssistant(), memory=None)
    
    assert engine.memory is None
    
    # Should still process, but memory commands should fail gracefully
    resp = engine.process("remember key=value")
    assert "not connected" in resp.text.lower()


# ============================================================================
# Remember Command Tests
# ============================================================================

def test_remember_stores_key_value(tmp_path) -> None:
    """Verify 'remember key=value' stores data."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    resp = engine.process("remember favorite_color=blue")
    
    assert resp.route.intent == Intent.MEMORY
    assert "stored" in resp.text.lower()
    assert "favorite_color" in resp.text
    assert mem.get("favorite_color") == "blue"


def test_remember_with_spaces_in_value(tmp_path) -> None:
    """Verify remember handles values with spaces."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    resp = engine.process("remember full_name=Alice Smith")
    
    assert resp.route.intent == Intent.MEMORY
    assert mem.get("full_name") == "Alice Smith"


def test_remember_with_special_characters(tmp_path) -> None:
    """Verify remember handles special characters in values."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    resp = engine.process("remember email=user@example.com")
    
    assert resp.route.intent == Intent.MEMORY
    assert mem.get("email") == "user@example.com"


def test_remember_malformed_command(tmp_path) -> None:
    """Verify malformed remember command fails gracefully."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    resp = engine.process("remember no_equals_here")
    
    assert resp.route.intent == Intent.MEMORY
    assert "couldn't understand" in resp.text.lower()
    assert len(mem.all()) == 0


# ============================================================================
# Recall/Retrieve Command Tests
# ============================================================================

def test_recall_retrieves_stored_value(tmp_path) -> None:
    """Verify 'What is key?' retrieves stored value."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    mem.set("favorite_color", "blue")
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    resp = engine.process("What is favorite_color?")
    
    assert resp.route.intent == Intent.MEMORY
    assert "blue" in resp.text


def test_recall_missing_key(tmp_path) -> None:
    """Verify recall for missing key returns appropriate message."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    resp = engine.process("What is missing_key?")
    
    assert resp.route.intent == Intent.MEMORY
    assert "don't recall" in resp.text.lower() or "recall" in resp.text.lower()


def test_recall_with_punctuation_variants(tmp_path) -> None:
    """Verify recall works with different punctuation."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    mem.set("name", "Alice")
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    # Test with question mark
    resp = engine.process("What is name?")
    assert "Alice" in resp.text
    
    # Test with period
    resp = engine.process("What is name.")
    assert "Alice" in resp.text


# ============================================================================
# Forget Command Tests
# ============================================================================

def test_forget_removes_key(tmp_path) -> None:
    """Verify 'forget key' removes stored data."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    mem.set("secret", "password123")
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    # Verify it exists
    assert mem.get("secret") == "password123"
    
    # Forget it
    resp = engine.process("forget secret")
    
    assert resp.route.intent == Intent.MEMORY
    assert "forgot" in resp.text.lower()
    assert "secret" in resp.text
    assert mem.get("secret") is None


def test_forget_missing_key(tmp_path) -> None:
    """Verify forget for missing key returns appropriate message."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    resp = engine.process("forget nonexistent_key")
    
    assert resp.route.intent == Intent.MEMORY
    assert "don't have any memory" in resp.text.lower() or "memory of" in resp.text.lower()


def test_forget_with_punctuation(tmp_path) -> None:
    """Verify forget works with trailing punctuation."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    mem.set("temp_data", "value")
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    # With question mark
    resp = engine.process("forget temp_data?")
    assert mem.get("temp_data") is None
    
    # Re-add for next test
    mem.set("temp_data", "value")
    
    # With period
    resp = engine.process("forget temp_data.")
    assert mem.get("temp_data") is None


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================

def test_complete_workflow(tmp_path) -> None:
    """Test complete remember-recall-forget workflow."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    # Remember
    resp = engine.process("remember project_status=active")
    assert resp.route.intent == Intent.MEMORY
    assert "stored" in resp.text.lower()
    
    # Recall
    resp = engine.process("What is project_status?")
    assert resp.route.intent == Intent.MEMORY
    assert "active" in resp.text
    
    # Forget
    resp = engine.process("forget project_status")
    assert resp.route.intent == Intent.MEMORY
    assert "forgot" in resp.text.lower()
    
    # Verify gone
    resp = engine.process("What is project_status?")
    assert "active" not in resp.text


def test_multiple_keys_in_memory(tmp_path) -> None:
    """Verify engine can store and retrieve multiple keys."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    # Store multiple values
    engine.process("remember name=Alice")
    engine.process("remember age=30")
    engine.process("remember city=New York")
    
    # Retrieve all
    assert mem.get("name") == "Alice"
    assert mem.get("age") == "30"
    assert mem.get("city") == "New York"
    
    # Forget one
    engine.process("forget age")
    
    # Verify others remain
    assert mem.get("name") == "Alice"
    assert mem.get("age") is None
    assert mem.get("city") == "New York"


def test_router_recognizes_forget_keyword(tmp_path) -> None:
    """Verify router routes 'forget' commands to MEMORY intent."""
    mem = Memory(path=str(tmp_path / "mem.json"))
    mem.set("test_key", "test_value")
    engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
    
    # Process should route to MEMORY intent
    resp = engine.process("forget test_key")
    
    assert resp.route.intent == Intent.MEMORY
    assert resp.route.reason == "Request contains memory-related language."
