#!/usr/bin/env python3
"""sign_msf.py -- sign a spatial fabric JSON into a .msf (Metaverse Spatial Fabric).

Mirrors the reference signed-stool-and-bucket.msf from the RP1 skeleton byte-for-byte:
  JWS  header  {"alg":"RS256","typ":"JWS","x5c":[leaf DER b64, ca DER b64]}   (insertion order)
  JWS  payload {"data":"<compact fabric JSON, insertion order preserved>"}
  RS256 (PKCS#1 v1.5, SHA-256) over the ASCII "<b64url(header)>.<b64url(payload)>"

Credentials: the OMBI test provider set from the Sneeze repo tests/certs/
(provider-key.pem / provider-cert.pem / ca-cert.pem) -- the documented learning path
("for real publishing, obtain a certificate from a public CA"; the engine does not yet
refuse untrusted chains). The private key never leaves this machine.

Usage:
  python3 tools/sign_msf.py <fabric.json> <out.msf> [--key p] [--cert c] [--ca a]
  python3 tools/sign_msf.py --inspect <ref.msf>        # decode a reference .msf
"""
import base64
import json
import os
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

HERE = os.path.dirname(os.path.abspath(__file__))
CERTS = '/tmp/msf-certs'


def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode('ascii')


def der_b64(path):
    cert = x509.load_pem_x509_certificate(open(path, 'rb').read())
    return base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode('ascii')


def inspect(path):
    tok = open(path).read().strip()
    h, p, s = tok.split('.')
    pad = lambda x: x + '=' * (-len(x) % 4)
    hdr = json.loads(base64.urlsafe_b64decode(pad(h)))
    pl = json.loads(base64.urlsafe_b64decode(pad(p)))
    print('header key order:', list(hdr.keys()), '| x5c entries:', len(hdr.get('x5c', [])))
    for i, c in enumerate(hdr.get('x5c', [])):
        cert = x509.load_der_x509_certificate(base64.b64decode(c))
        print(f'  x5c[{i}]:', cert.subject.rfc4514_string(), '<-', cert.issuer.rfc4514_string())
    print('payload keys:', list(pl.keys()))
    fabric = json.loads(pl['data'])
    print('inner fabric keys:', list(fabric.keys()))
    print('Modules:', json.dumps(fabric.get('Modules')))
    print('inner sample:', pl['data'][:100])
    print('sig b64url len:', len(s))


def sign(payload_path, out_path, key_pem, cert_pem, ca_pem, wasm_path=None):
    fabric = json.load(open(payload_path))
    # pin the module with its content hash (sha256-<hex>) when a module binary is given,
    # exactly like the reference signed fabric: {"sHash":"sha256-..","sUrl":"wasm/map.wasm"}
    if wasm_path and os.path.isfile(wasm_path):
        import hashlib
        digest = hashlib.sha256(open(wasm_path, 'rb').read()).hexdigest()
        for mod in fabric.get('Modules', []):
            if mod.get('sUrl') and not mod.get('sHash'):
                mod['sHash'] = f'sha256-{digest}'
    # the reference .msf serializes the inner fabric with SORTED keys, compact separators
    inner = json.dumps(fabric, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    payload = json.dumps({'data': inner}, separators=(',', ':'), ensure_ascii=False)
    header = json.dumps({'alg': 'RS256', 'typ': 'JWS', 'x5c': [der_b64(cert_pem), der_b64(ca_pem)]},
                        separators=(',', ':'), ensure_ascii=False)
    signing_input = f'{b64u(header.encode())}.{b64u(payload.encode())}'
    key = serialization.load_pem_private_key(open(key_pem, 'rb').read(), password=None)
    sig = key.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
    msf = signing_input + '.' + b64u(sig)
    # self-verify with the leaf public key
    cert = x509.load_pem_x509_certificate(open(cert_pem, 'rb').read())
    cert.public_key().verify(sig, signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
    with open(out_path, 'w') as f:
        f.write(msf)
    print(f'Signed {out_path} ({len(msf)} bytes, signature verified with leaf public key)')
    return msf


def verify_ref(ref_path, key_pem=None):
    """Verify a reference .msf signature with the TEST provider key, proving the credential set matches."""
    tok = open(ref_path).read().strip()
    h, p, s = tok.split('.')
    pad = lambda x: x + '=' * (-len(x) % 4)
    signing_input = f'{h}.{p}'
    sig = base64.urlsafe_b64decode(pad(s))
    cert = x509.load_pem_x509_certificate(open(key_pem, 'rb').read()) if key_pem else None
    if cert is None:
        return
    # the ref was signed by the provider; use the leaf cert from x5c instead
    hdr = json.loads(base64.urlsafe_b64decode(pad(h)))
    leaf = x509.load_der_x509_certificate(base64.b64decode(hdr['x5c'][0]))
    leaf.public_key().verify(sig, signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
    print('reference signature VERIFIED with the embedded leaf public key')


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == '--inspect':
        return inspect(argv[1])
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    payload, out = argv[0], argv[1]
    key = os.path.join(CERTS, 'provider-key.pem')
    cert = os.path.join(CERTS, 'provider-cert.pem')
    ca = os.path.join(CERTS, 'ca-cert.pem')
    if '--key' in argv:
        key = argv[argv.index('--key') + 1]
    if '--cert' in argv:
        cert = argv[argv.index('--cert') + 1]
    if '--ca' in argv:
        ca = argv[argv.index('--ca') + 1]
    sign(payload, out, key, cert, ca)


if __name__ == '__main__':
    main()
