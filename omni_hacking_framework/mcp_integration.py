from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, conbytes
from cryptography.hazmat.primitives.asymmetric import ed25519
import msgpack
import time
import struct
from cryptography.exceptions import InvalidSignature

class MCPHeader(BaseModel):
    protocol_version: int = Field(0x01, ge=0x01, le=0x7F)
    context_class: int = Field(..., ge=0x00, le=0xFF)
    temporal_validity: int = Field(
        default_factory=lambda: int(time.time() + 300),
        description="Unix timestamp with 5min default TTL"
    )
    spatial_context: bytes = Field(
        ...,
        min_length=16,
        max_length=64,
        description="Geohash or GPS fix compressed with LZ4"
    )

    def serialize(self) -> bytes:
        return msgpack.packb(self.dict(), use_bin_type=True)

class MCPSecurityFooter(BaseModel):
    signature: conbytes(min_length=64, max_length=64)
    public_key: conbytes(min_length=32, max_length=32)
    key_rotation_index: int = Field(..., ge=0)

    def serialize(self) -> bytes:
        return msgpack.packb(self.dict(), use_bin_type=True)

class MCPPayload(BaseModel):
    model_identifier: str = Field(..., max_length=32)
    context_window: Dict[str, Any]
    execution_constraints: Dict[str, float]
    lineage_proof: Optional[bytes] = None

    def serialize(self) -> bytes:
        return msgpack.packb(self.dict(), use_bin_type=True)

class MCPPacket:
    def __init__(self, header: MCPHeader, payload: MCPPayload, footer: MCPSecurityFooter):
        self.header = header
        self.payload = payload
        self.footer = footer

    def serialize(self) -> bytes:
        packet_data = {
            'header': self.header.dict(),
            'payload': self.payload.dict(),
            'footer': self.footer.dict()
        }
        return msgpack.packb(packet_data, use_bin_type=True)

    @classmethod
    def deserialize(cls, data: bytes) -> 'MCPPacket':
        unpacked = msgpack.unpackb(data, raw=False)
        return cls(
            header=MCPHeader(**unpacked['header']),
            payload=MCPPayload(**unpacked['payload']),
            footer=MCPSecurityFooter(**unpacked['footer'])
        )

    def verify_signature(self) -> bool:
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(self.footer.public_key)
        try:
            public_key.verify(
                self.footer.signature,
                self._signing_payload()
            )
            return True
        except InvalidSignature:
            return False

    def _signing_payload(self) -> bytes:
        return (
            self.header.serialize() +
            self.payload.serialize() +
            struct.pack('!Q', self.footer.key_rotation_index)
        )
