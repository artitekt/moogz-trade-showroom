"""
Mock AES-256 Encryption Module
Simulated encryption for demo purposes
"""

import base64
import secrets
from typing import Dict, Any, Optional
from datetime import datetime


class EncryptionManager:
    """Mock encryption manager for demo purposes"""
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize mock encryption manager"""
        self.key = key or b"mock_key_32_bytes_long_for_demo_purposes"
    
    def encrypt(self, plaintext: str) -> Dict[str, str]:
        """Mock encryption that returns simulated encrypted data"""
        mock_ciphertext = base64.b64encode(f"encrypted_{plaintext}".encode()).decode()
        mock_nonce = secrets.token_hex(12)
        mock_tag = secrets.token_hex(16)
        
        return {
            "ciphertext": mock_ciphertext,
            "nonce": mock_nonce,
            "tag": mock_tag,
            "timestamp": datetime.now().isoformat()
        }
    
    def decrypt(self, ciphertext: str, nonce: str, tag: str) -> str:
        """Mock decryption that returns simulated plaintext"""
        # In demo mode, just decode the mock format
        if "encrypted_" in ciphertext:
            decoded = base64.b64decode(ciphertext).decode()
            return decoded.replace("encrypted_", "")
        return "decrypted_mock_data"
