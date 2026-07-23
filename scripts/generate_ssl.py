import os
import datetime
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ssl')
CERT_PATH = os.path.join(OUT_DIR, 'cert.pem')
KEY_PATH = os.path.join(OUT_DIR, 'key.pem')

def generate():
    os.makedirs(OUT_DIR, exist_ok=True)

    if os.path.exists(CERT_PATH) and os.path.exists(KEY_PATH):
        print(f'Certificado ja existe em {OUT_DIR}')
        return

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, 'BR'),
        x509.NameAttribute(NameOID.COMMON_NAME, 'sginf.local'),
    ])

    sans = [
        x509.DNSName('localhost'),
        x509.DNSName('sginf.local'),
        x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
    ]
    server_ip = os.environ.get('SERVER_IP')
    if server_ip:
        sans.append(x509.IPAddress(ipaddress.IPv4Address(server_ip)))

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName(sans), critical=False)
        .sign(key, hashes.SHA256(), backend=default_backend())
    )

    with open(KEY_PATH, 'wb') as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(CERT_PATH, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f'Certificado gerado em {OUT_DIR}')
    print(f'  Cert: {CERT_PATH}')
    print(f'  Key:  {KEY_PATH}')


if __name__ == '__main__':
    generate()
