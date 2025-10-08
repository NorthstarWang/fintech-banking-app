"""
Multi-Factor Authentication with TOTP (Time-based One-Time Password) implementation.
Provides secure second factor authentication for banking applications.
"""
import base64
import io
import secrets
import time
from typing import Dict, List, Optional, Tuple

import pyotp
import qrcode
from fastapi import HTTPException, status


class MFAManager:
    """Comprehensive MFA manager with TOTP, backup codes, and device trust."""

    def __init__(self):
        # Store MFA data - in production, use database
        self.mfa_data: Dict[int, Dict] = {}  # user_id -> mfa_config
        self.pending_setups: Dict[str, Dict] = {}  # temp_token -> setup_data
        self.trusted_devices: Dict[int, List[str]] = {}  # user_id -> device_fingerprints
        self.backup_codes: Dict[int, List[str]] = {}  # user_id -> backup_codes

    def _generate_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    def _generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for account recovery."""
        return [secrets.token_hex(4).upper() for _ in range(count)]

    def _get_device_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """Create a device fingerprint from user agent and IP."""
        import hashlib
        data = f"{user_agent}:{ip_address}".encode()
        return hashlib.sha256(data).hexdigest()[:16]

    def is_mfa_enabled(self, user_id: int) -> bool:
        """Check if MFA is enabled for a user."""
        return user_id in self.mfa_data and self.mfa_data[user_id].get('enabled', False)

    def is_device_trusted(self, user_id: int, user_agent: str, ip_address: str) -> bool:
        """Check if the current device is trusted."""
        if not self.is_mfa_enabled(user_id):
            return True

        device_fingerprint = self._get_device_fingerprint(user_agent, ip_address)
        trusted_devices = self.trusted_devices.get(user_id, [])
        return device_fingerprint in trusted_devices

    def setup_mfa(self, user_id: int, username: str, email: str) -> Dict[str, str]:
        """Initialize MFA setup for a user."""
        secret = self._generate_secret()
        backup_codes = self._generate_backup_codes()

        # Create setup token for verification
        setup_token = secrets.token_urlsafe(32)

        # Store temporary setup data
        self.pending_setups[setup_token] = {
            'user_id': user_id,
            'secret': secret,
            'backup_codes': backup_codes,
            'created_at': time.time(),
            'username': username,
            'email': email
        }

        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name="BankFlow - Secure Banking"
        )

        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Convert QR code to base64 string
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()

        return {
            'setup_token': setup_token,
            'secret': secret,  # For manual entry
            'qr_code': f"data:image/png;base64,{qr_code_data}",
            'backup_codes': backup_codes
        }

    def verify_and_enable_mfa(self, setup_token: str, verification_code: str) -> bool:
        """Verify TOTP code and enable MFA."""
        if setup_token not in self.pending_setups:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired setup token"
            )

        setup_data = self.pending_setups[setup_token]

        # Check if setup token expired (15 minutes)
        if time.time() - setup_data['created_at'] > 900:
            del self.pending_setups[setup_token]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Setup token has expired. Please restart MFA setup."
            )

        # Verify TOTP code
        totp = pyotp.TOTP(setup_data['secret'])
        if not totp.verify(verification_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )

        # Enable MFA for the user
        user_id = setup_data['user_id']
        self.mfa_data[user_id] = {
            'enabled': True,
            'secret': setup_data['secret'],
            'enabled_at': time.time(),
            'username': setup_data['username'],
            'email': setup_data['email']
        }

        # Store backup codes
        self.backup_codes[user_id] = setup_data['backup_codes']

        # Clean up pending setup
        del self.pending_setups[setup_token]

        return True

    def verify_totp(self, user_id: int, code: str) -> bool:
        """Verify TOTP code for an enabled MFA user."""
        if not self.is_mfa_enabled(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this user"
            )

        mfa_config = self.mfa_data[user_id]
        totp = pyotp.TOTP(mfa_config['secret'])

        # Allow for some time drift (±1 window = ±30 seconds)
        return totp.verify(code, valid_window=1)

    def verify_backup_code(self, user_id: int, backup_code: str) -> bool:
        """Verify and consume a backup code."""
        if not self.is_mfa_enabled(user_id):
            return False

        user_backup_codes = self.backup_codes.get(user_id, [])
        backup_code_upper = backup_code.upper()

        if backup_code_upper in user_backup_codes:
            # Remove used backup code
            user_backup_codes.remove(backup_code_upper)
            return True

        return False

    def trust_device(self, user_id: int, user_agent: str, ip_address: str, trust_duration_days: int = 30):
        """Mark a device as trusted for the specified duration."""
        device_fingerprint = self._get_device_fingerprint(user_agent, ip_address)

        if user_id not in self.trusted_devices:
            self.trusted_devices[user_id] = []

        # Add device with expiration timestamp
        device_info = f"{device_fingerprint}:{int(time.time() + (trust_duration_days * 86400))}"

        # Remove if already exists (update expiration)
        self.trusted_devices[user_id] = [
            d for d in self.trusted_devices[user_id]
            if not d.startswith(device_fingerprint + ":")
        ]

        self.trusted_devices[user_id].append(device_info)

    def revoke_device_trust(self, user_id: int, user_agent: str, ip_address: str):
        """Revoke trust for a specific device."""
        if user_id not in self.trusted_devices:
            return

        device_fingerprint = self._get_device_fingerprint(user_agent, ip_address)
        self.trusted_devices[user_id] = [
            d for d in self.trusted_devices[user_id]
            if not d.startswith(device_fingerprint + ":")
        ]

    def revoke_all_device_trust(self, user_id: int):
        """Revoke trust for all devices."""
        if user_id in self.trusted_devices:
            self.trusted_devices[user_id] = []

    def disable_mfa(self, user_id: int):
        """Disable MFA for a user."""
        if user_id in self.mfa_data:
            del self.mfa_data[user_id]
        if user_id in self.backup_codes:
            del self.backup_codes[user_id]
        if user_id in self.trusted_devices:
            del self.trusted_devices[user_id]

    def generate_new_backup_codes(self, user_id: int) -> List[str]:
        """Generate new backup codes, invalidating old ones."""
        if not self.is_mfa_enabled(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this user"
            )

        new_codes = self._generate_backup_codes()
        self.backup_codes[user_id] = new_codes
        return new_codes

    def get_mfa_status(self, user_id: int) -> Dict:
        """Get MFA status and statistics for a user."""
        if not self.is_mfa_enabled(user_id):
            return {
                'enabled': False,
                'trusted_devices': 0,
                'backup_codes_remaining': 0
            }

        trusted_count = len(self.trusted_devices.get(user_id, []))
        backup_count = len(self.backup_codes.get(user_id, []))

        return {
            'enabled': True,
            'enabled_at': self.mfa_data[user_id].get('enabled_at'),
            'trusted_devices': trusted_count,
            'backup_codes_remaining': backup_count
        }

    def cleanup_expired_devices(self):
        """Remove expired trusted devices."""
        current_time = time.time()

        for user_id, devices in self.trusted_devices.items():
            valid_devices = []
            for device_info in devices:
                if ':' in device_info:
                    fingerprint, expiration_str = device_info.rsplit(':', 1)
                    try:
                        expiration = int(expiration_str)
                        if current_time < expiration:
                            valid_devices.append(device_info)
                    except ValueError:
                        # Invalid format, remove
                        continue

            self.trusted_devices[user_id] = valid_devices

    def require_mfa_verification(self, user_id: int, user_agent: str, ip_address: str) -> bool:
        """Check if MFA verification is required for this login."""
        if not self.is_mfa_enabled(user_id):
            return False

        # Check if device is trusted
        if self.is_device_trusted(user_id, user_agent, ip_address):
            return False

        return True


# Global MFA manager instance
mfa_manager = MFAManager()


class MFARequired(HTTPException):
    """Custom exception for MFA requirement."""

    def __init__(self, detail: str = "Multi-factor authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "MFA"}
        )