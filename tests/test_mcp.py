import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from omni_hacking_framework.mcp_security import MCPKeyManager
from omni_hacking_framework.mcp_attack_orchestrator import MCPCompliantAttackSystem
from omni_hacking_framework.mcp_integration import MCPHeader, MCPPayload


def test_context_key_derivation():
    manager = MCPKeyManager()
    key = manager.derive_context_key(b'context')
    assert isinstance(key, bytes)
    assert len(key) == 32


def test_sign_packet_public_key_length():
    system = MCPCompliantAttackSystem(MCPKeyManager().current_key)
    header = MCPHeader(context_class=1, spatial_context=b'0' * 16)
    payload = MCPPayload(model_identifier='m', context_window={}, execution_constraints={})
    footer = system._sign_packet(header, payload)
    assert len(footer.public_key) == 32
