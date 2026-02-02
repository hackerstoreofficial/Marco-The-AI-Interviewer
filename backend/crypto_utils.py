"""
Cryptography utilities for encrypting/decrypting sensitive data
Uses Fernet symmetric encryption for API keys
"""
import os
import logging
from cryptography.fernet import Fernet
import base64
import hashlib

logger = logging.getLogger(__name__)


class CryptoService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        """Initialize crypto service with encryption key"""
        # Get encryption key from environment or generate one
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        
        if not encryption_key:
            # Generate a key from a default secret (NOT SECURE for production!)
            # In production, use a proper secret management system
            default_secret = "marco-ai-interview-default-secret-key-change-in-production"
            logger.warning("ENCRYPTION_KEY not set in environment. Using default (NOT SECURE for production!)")
            
            # Derive a Fernet key from the secret
            key_material = hashlib.sha256(default_secret.encode()).digest()
            encryption_key = base64.urlsafe_b64encode(key_material)
        else:
            # Ensure the key is properly formatted for Fernet
            if len(encryption_key) < 32:
                # Pad the key if too short
                key_material = hashlib.sha256(encryption_key.encode()).digest()
                encryption_key = base64.urlsafe_b64encode(key_material)
            elif not isinstance(encryption_key, bytes):
                encryption_key = encryption_key.encode()
        
        self.cipher = Fernet(encryption_key)
        logger.info("CryptoService initialized")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        try:
            if not plaintext:
                return ""
            
            # Encrypt the plaintext
            encrypted_bytes = self.cipher.encrypt(plaintext.encode())
            
            # Return as base64 string for database storage
            return encrypted_bytes.decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            ciphertext: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        try:
            if not ciphertext:
                return ""
            
            # Decrypt the ciphertext
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
            
            # Return as string
            return decrypted_bytes.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise


# Singleton instance
_crypto_service = None


def get_crypto_service() -> CryptoService:
    """Get or create singleton crypto service instance"""
    global _crypto_service
    if _crypto_service is None:
        _crypto_service = CryptoService()
    return _crypto_service


# Convenience functions
def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key"""
    return get_crypto_service().encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key"""
    return get_crypto_service().decrypt(encrypted_key)
