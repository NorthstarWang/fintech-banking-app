"""mTLS (mutual TLS) configuration for service-to-service communication."""
import ssl
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class mTLSConfig:
    """Configuration for mutual TLS between services."""

    def __init__(
        self,
        cert_file: str = None,
        key_file: str = None,
        ca_file: str = None,
        verify_peer: bool = True
    ):
        """
        Initialize mTLS configuration.

        Args:
            cert_file: Path to service certificate
            key_file: Path to service private key
            ca_file: Path to CA certificate for verification
            verify_peer: Whether to verify peer certificates
        """
        self.cert_file = cert_file or os.getenv("MTLS_CERT_FILE", "/etc/mtls/certs/service.crt")
        self.key_file = key_file or os.getenv("MTLS_KEY_FILE", "/etc/mtls/certs/service.key")
        self.ca_file = ca_file or os.getenv("MTLS_CA_FILE", "/etc/mtls/certs/ca.crt")
        self.verify_peer = verify_peer

        self._validate_files()

    def _validate_files(self):
        """Validate that certificate files exist."""
        if not Path(self.cert_file).exists():
            logger.warning(f"Certificate file not found: {self.cert_file}")
        if not Path(self.key_file).exists():
            logger.warning(f"Key file not found: {self.key_file}")
        if self.verify_peer and not Path(self.ca_file).exists():
            logger.warning(f"CA file not found: {self.ca_file}")

    def get_ssl_context(self, server: bool = False) -> ssl.SSLContext:
        """
        Get SSL context for service.

        Args:
            server: If True, create server context; if False, create client context

        Returns:
            Configured SSL context
        """
        if server:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(self.cert_file, self.key_file)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.load_cert_chain(self.cert_file, self.key_file)

        if self.verify_peer:
            context.load_verify_locations(self.ca_file)
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            context.verify_mode = ssl.CERT_NONE
            context.check_hostname = False

        # Security best practices
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers('ECDHE+AESGCM:DHE+AESGCM:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4')

        logger.info("SSL context configured successfully")
        return context

    @staticmethod
    def generate_self_signed_cert(
        cert_file: str,
        key_file: str,
        service_name: str = "service",
        days: int = 365
    ):
        """
        Generate self-signed certificate for testing.

        Args:
            cert_file: Path to save certificate
            key_file: Path to save private key
            service_name: Common name for certificate
            days: Days until certificate expires
        """
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            from datetime import datetime, timedelta
            import ipaddress

            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Organization"),
                x509.NameAttribute(NameOID.COMMON_NAME, service_name),
            ])

            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=days)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(service_name),
                    x509.DNSName(f"{service_name}.local"),
                    x509.DNSName(f"{service_name}.svc.cluster.local"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256(), default_backend())

            # Save certificate
            os.makedirs(os.path.dirname(cert_file), exist_ok=True)
            os.makedirs(os.path.dirname(key_file), exist_ok=True)

            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            with open(key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            logger.info(f"Generated self-signed certificate for {service_name}")

        except ImportError:
            logger.error("cryptography library not installed. Install with: pip install cryptography")


# Global mTLS config
_mtls_config: Optional[mTLSConfig] = None


def get_mtls_config() -> mTLSConfig:
    """Get or create global mTLS config."""
    global _mtls_config
    if _mtls_config is None:
        _mtls_config = mTLSConfig()
    return _mtls_config


def init_mtls_config(
    cert_file: str = None,
    key_file: str = None,
    ca_file: str = None,
    verify_peer: bool = True
) -> mTLSConfig:
    """Initialize global mTLS config."""
    global _mtls_config
    _mtls_config = mTLSConfig(cert_file, key_file, ca_file, verify_peer)
    return _mtls_config
