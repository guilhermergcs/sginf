import os
import sys
from app import create_app

CERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl', 'cert.pem')
KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl', 'key.pem')

app = create_app()

if __name__ == '__main__':
    https = os.path.exists(CERT_PATH) and os.path.exists(KEY_PATH)

    if https:
        default_port = '443' if sys.platform == 'win32' else '8443'
        port = int(os.environ.get('PORT', default_port))
        host = os.environ.get('HOST', '0.0.0.0')
        print(f'[*] HTTPS em https://{host}:{port}')
        if sys.platform != 'win32' and port == 443:
            print('[*] Porta 443 requer root. Use PORT=8443 ou sudo.')
        app.run(host=host, port=port, ssl_context=(CERT_PATH, KEY_PATH), debug=True)
    else:
        print('[!] Certificado SSL nao encontrado. Execute: python scripts/generate_ssl.py')
        print('[!] Iniciando sem HTTPS...')
        app.run(host='0.0.0.0', port=5000, debug=True)
