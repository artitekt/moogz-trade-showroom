# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Encryption
# Licensing: Contact [Your Email]

"""
AES-256 Encryption Module
Military-grade encryption for sensitive trading data
"""

import os
import base64
import hashlib
import hmac
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from typing import Dict, Any, Optional
import json
from datetime import datetime


class EncryptionManager:
    """Enterprise-grade encryption manager for trading data"""
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryption manager
        
        Args:
            key: 32-byte encryption key. If None, generates a new key.
        """
        self.key = key or secrets.token_bytes(32)
        self.backend = default_backend()
    
    def encrypt(self, plaintext: str) -> Dict[str, str]:
        """
        Encrypt plaintext using AES-256-GCM
        
        Args:
            plaintext: Data to encrypt
            
        Returns:
            Dictionary with ciphertext, nonce, and HMAC
        """
        # Generate random nonce
        nonce = secrets.token_bytes(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Encrypt data
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Generate HMAC
        hmac_key = hashlib.sha256(self.key).digest()
        message = nonce + ciphertext + encryptor.tag
        signature = hmac.new(hmac_key, message, hashlib.sha256).hexdigest()
        
        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "tag": base64.b64encode(encryptor.tag).decode(),
            "hmac": signature,
            "timestamp": datetime.now().isoformat()
        }
    
    def decrypt(self, encrypted_data: Dict[str, str]) -> str:
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data: Dictionary with ciphertext, nonce, tag, and HMAC
            
        Returns:
            Decrypted plaintext
        """
        # Verify HMAC
        hmac_key = hashlib.sha256(self.key).digest()
        ciphertext = base64.b64decode(encrypted_data["ciphertext"])
        nonce = base64.b64decode(encrypted_data["nonce"])
        tag = base64.b64decode(encrypted_data["tag"])
        message = nonce + ciphertext + tag
        expected_hmac = hmac.new(hmac_key, message, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(expected_hmac, encrypted_data["hmac"]):
            raise ValueError("HMAC verification failed - data may be tampered")
        
        # Decrypt data
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce, tag),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext.decode()
    
    def generate_key(self) -> str:
        """Generate a new encryption key"""
        return base64.b64encode(secrets.token_bytes(32)).decode()
    
    def rotate_key(self, old_key: bytes) -> bytes:
        """Rotate encryption key"""
        self.key = secrets.token_bytes(32)
        return self.key


# Convenience functions for backward compatibility
def encrypt_data(plaintext: str, key: Optional[bytes] = None) -> Dict[str, str]:
    """Encrypt data using default encryption manager"""
    manager = EncryptionManager(key)
    return manager.encrypt(plaintext)


def decrypt_data(encrypted_data: Dict[str, str], key: bytes) -> str:
    """Decrypt data using default encryption manager"""
    manager = EncryptionManager(key)
    return manager.decrypt(encrypted_data)
