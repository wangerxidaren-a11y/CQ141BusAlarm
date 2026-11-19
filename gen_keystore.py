#!/usr/bin/env python3
"""Rebuild the fixed signing keystore from two small repo secrets.

Signer identity = an EC P-256 key pair plus a self-signed certificate,
both generated once and then frozen:

  SIGNING_SEED      64 hex chars: the EC private scalar
  SIGNING_CERT_B64  base64 of the certificate (DER), generated once
                    from that same key

Every CI run reassembles the identical key + certificate into a
PKCS12 keystore, so every build is signed by the identical signer
and new versions install over old ones.

Outputs (in SIGNING_OUT_DIR, default ./signing-out):
  cq141-fixed.p12  PKCS12 keystore, alias "cq141"
  signing.env      KEYSTORE_PASSWORD / KEY_PASSWORD / KEY_ALIAS lines
"""

import base64
import hashlib
import os
import sys

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import pkcs12

ALIAS = "cq141"
P256_ORDER = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551


def main() -> None:
    seed_hex = os.environ.get("SIGNING_SEED", "").strip()
    cert_b64 = os.environ.get("SIGNING_CERT_B64", "").strip()
    if len(seed_hex) != 64 or not cert_b64:
        print("SIGNING_SEED (64 hex) and SIGNING_CERT_B64 are required", file=sys.stderr)
        sys.exit(1)
    seed = bytes.fromhex(seed_hex)
    cert = x509.load_der_x509_certificate(base64.b64decode(cert_b64))

    scalar = int.from_bytes(seed, "big") % (P256_ORDER - 1) + 1
    key = ec.derive_private_key(scalar, ec.SECP256R1())
    if key.public_key().public_numbers() != cert.public_key().public_numbers():
        print("seed does not match certificate public key", file=sys.stderr)
        sys.exit(1)

    password = hashlib.sha256(seed + b":keystore").hexdigest()

    p12 = pkcs12.serialize_key_and_certificates(
        name=ALIAS.encode(),
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode()),
    )

    out_dir = os.environ.get("SIGNING_OUT_DIR", "signing-out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "cq141-fixed.p12"), "wb") as f:
        f.write(p12)
    with open(os.path.join(out_dir, "signing.env"), "w", encoding="utf-8") as f:
        f.write(f"KEYSTORE_PASSWORD={password}\n")
        f.write(f"KEY_PASSWORD={password}\n")
        f.write(f"KEY_ALIAS={ALIAS}\n")

    from cryptography.hazmat.primitives import hashes

    print("cert sha256:", cert.fingerprint(hashes.SHA256()).hex())


if __name__ == "__main__":
    main()
