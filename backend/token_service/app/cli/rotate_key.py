#!/usr/bin/env python3
"""CLI to rotate the signing key. Run: python -m app.cli.rotate_key"""
import sys

from app.config import get_settings
from app.database import SessionLocal
from app.models import SigningKey
from app.services.signing_service import create_signing_key_id, generate_ed25519_keypair


def main() -> int:
    settings = get_settings()
    if not settings.DATABASE_URL:
        print("Error: DATABASE_URL not set", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        # Deactivate current active key(s)
        db.query(SigningKey).filter(SigningKey.is_active.is_(True)).update(
            {"is_active": False}
        )

        # Generate new keypair
        private_b64, public_b64 = generate_ed25519_keypair()
        key_id = create_signing_key_id()

        new_key = SigningKey(
            id=key_id,
            algorithm="Ed25519",
            private_key=private_b64,
            public_key=public_b64,
            is_active=True,
        )
        db.add(new_key)
        db.commit()
        print(f"Rotated signing key: {key_id}")
        return 0
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
