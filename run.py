import os
from app import create_app

CERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl', 'cert.pem')
KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl', 'key.pem')

app = create_app()

if __name__ == '__main__':
    if os.path.exists(CERT_PATH) and os.path.exists(KEY_PATH):
        print(f'[*] HTTPS em https://0.0.0.0:443')
        app.run(host='0.0.0.0', port=443, ssl_context=(CERT_PATH, KEY_PATH), debug=True)
    else:
        print('[!] Certificado SSL nao encontrado. Execute: python scripts/generate_ssl.py')
        print('[!] Iniciando sem HTTPS...')
        app.run(host='0.0.0.0', port=5000, debug=True)
