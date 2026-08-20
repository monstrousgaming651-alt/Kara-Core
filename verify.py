#!/usr/bin/env python3
"""Verification script to test all memory functionality."""

import sys
import subprocess
import json
from pathlib import Path
from tempfile import TemporaryDirectory

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import KaraEngine
from core.memory import Memory
from core.router import Intent


class DummyAssistant:
    """Dummy assistant for testing."""
    def send_message(self, text: str) -> str:
        return "dummy response"


def test_memory_persistence():
    """Test 1: Memory persistence across instances."""
    with TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "mem.json")
        
        # Create first instance and store data
        mem1 = Memory(path=path)
        mem1.set("name", "Alice")
        mem1.set("age", 30)
        
        # Create second instance and verify data is loaded
        mem2 = Memory(path=path)
        assert mem2.get("name") == "Alice"
        assert mem2.get("age") == 30
        print("✓ Test 1 PASS: Memory persistence across instances")


def test_engine_memory_integration():
    """Test 2: KaraEngine accepts and exposes Memory."""
    with TemporaryDirectory() as tmp:
        mem = Memory(path=str(Path(tmp) / "mem.json"))
        engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
        
        assert engine.memory is mem
        print("✓ Test 2 PASS: Engine memory integration")


def test_remember_command():
    """Test 3: Remember command stores data."""
    with TemporaryDirectory() as tmp:
        mem = Memory(path=str(Path(tmp) / "mem.json"))
        engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
        
        resp = engine.process("remember favorite_color=blue")
        
        assert resp.route.intent == Intent.MEMORY
        assert "stored" in resp.text.lower()
        assert mem.get("favorite_color") == "blue"
        print("✓ Test 3 PASS: Remember command stores data")


def test_recall_command():
    """Test 4: Recall command retrieves data."""
    with TemporaryDirectory() as tmp:
        mem = Memory(path=str(Path(tmp) / "mem.json"))
        mem.set("favorite_color", "blue")
        engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
        
        resp = engine.process("What is favorite_color?")
        
        assert resp.route.intent == Intent.MEMORY
        assert "blue" in resp.text
        print("✓ Test 4 PASS: Recall command retrieves data")


def test_recall_missing_key():
    """Test 5: Recall handles missing keys gracefully."""
    with TemporaryDirectory() as tmp:
        mem = Memory(path=str(Path(tmp) / "mem.json"))
        engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
        
        resp = engine.process("What is missing_key?")
        
        assert resp.route.intent == Intent.MEMORY
        assert "don't recall" in resp.text.lower() or "recall" in resp.text.lower()
        print("✓ Test 5 PASS: Recall handles missing keys gracefully")


def test_forget_command():
    """Test 6: Forget command removes data."""
    with TemporaryDirectory() as tmp:
        mem = Memory(path=str(Path(tmp) / "mem.json"))
        mem.set("secret", "password123")
        engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
        
        resp = engine.process("forget secret")
        
        assert resp.route.intent == Intent.MEMORY
        assert "forgot" in resp.text.lower()
        assert mem.get("secret") is None
        print("✓ Test 6 PASS: Forget command removes data")


def test_forget_missing_key():
    """Test 7: Forget handles missing keys gracefully."""
    with TemporaryDirectory() as tmp:
        mem = Memory(path=str(Path(tmp) / "mem.json"))
        engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
        
        resp = engine.process("forget nonexistent_key")
        
        assert resp.route.intent == Intent.MEMORY
        assert "don't have any memory" in resp.text.lower() or "memory of" in resp.text.lower()
        print("✓ Test 7 PASS: Forget handles missing keys gracefully")


def test_router_forget_keyword():
    """Test 8: Router recognizes 'forget' as memory keyword."""
    with TemporaryDirectory() as tmp:
        mem = Memory(path=str(Path(tmp) / "mem.json"))
        mem.set("test_key", "test_value")
        engine = KaraEngine(assistant=DummyAssistant(), memory=mem)
        
        resp = engine.process("forget test_key")
        
        assert resp.route.intent == Intent.MEMORY
        print("✓ Test 8 PASS: Router recognizes forget keyword")


def test_complete_workflow():
    """Test 9: Complete remember-recall-forget workflow."""
    with TemporaryDirectory() as tmp:
        mem = Memory(path=str(Path(tmp) / "mem.json"))
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
        
        print("✓ Test 9 PASS: Complete workflow")


def test_memory_no_backend():
    """Test 10: Engine handles missing memory backend gracefully."""
    engine = KaraEngine(assistant=DummyAssistant(), memory=None)
    
    assert engine.memory is None
    
    resp = engine.process("remember key=value")
    assert "not connected" in resp.text.lower()
    print("✓ Test 10 PASS: Engine handles missing memory backend")


def run_manual_tests():
    """Run all manual integration tests."""
    print("\n" + "="*70)
    print("RUNNING MANUAL INTEGRATION TESTS")
    print("="*70 + "\n")
    
    try:
        test_memory_persistence()
        test_engine_memory_integration()
        test_remember_command()
        test_recall_command()
        test_recall_missing_key()
        test_forget_command()
        test_forget_missing_key()
        test_router_forget_keyword()
        test_complete_workflow()
        test_memory_no_backend()
        
        print("\n" + "="*70)
        print("✓ ALL MANUAL TESTS PASSED (10/10)")
        print("="*70 + "\n")
        return True
    except AssertionError as e:
        print(f"\n✗ MANUAL TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def run_pytest():
    """Run pytest suite."""
    print("\n" + "="*70)
    print("RUNNING PYTEST SUITE")
    print("="*70 + "\n")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=Path(__file__).parent
    )
    
    return result.returncode == 0


def run_compile_check():
    """Run compileall to check syntax."""
    print("\n" + "="*70)
    print("RUNNING COMPILE CHECK")
    print("="*70 + "\n")
    
    result = subprocess.run(
        [sys.executable, "-m", "compileall", "."],
        cwd=Path(__file__).parent
    )
    
    return result.returncode == 0


if __name__ == "__main__":
    manual_ok = run_manual_tests()
    pytest_ok = run_pytest()
    compile_ok = run_compile_check()
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"Manual Tests:  {'✓ PASS' if manual_ok else '✗ FAIL'}")
    print(f"Pytest Suite:  {'✓ PASS' if pytest_ok else '✗ FAIL'}")
    print(f"Compile Check: {'✓ PASS' if compile_ok else '✗ FAIL'}")
    print("="*70 + "\n")
    
    if manual_ok and pytest_ok and compile_ok:
        print("✓✓✓ ALL VERIFICATION CHECKS PASSED ✓✓✓\n")
        sys.exit(0)
    else:
        print("✗✗✗ SOME VERIFICATION CHECKS FAILED ✗✗✗\n")
        sys.exit(1)
