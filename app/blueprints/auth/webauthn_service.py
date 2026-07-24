import os
from webauthn import (
    generate_registration_options, verify_registration_response,
    generate_authentication_options, verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria, UserVerificationRequirement,
)
from flask import request, current_app
from app.db import get_db_connection
import secrets

def get_rp_id():
    return os.environ.get('RP_ID') or request.host.split(':')[0]

def get_origin():
    return request.scheme + '://' + request.host

def register_begin(user_id, username):
    challenge = secrets.token_bytes(32)
    options = generate_registration_options(
        rp_id=get_rp_id(),
        rp_name='SGINF',
        user_id=str(user_id).encode(),
        user_name=username,
        challenge=challenge,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    if 'webauthn_challenges' not in current_app.config:
        current_app.config['webauthn_challenges'] = {}
    current_app.config['webauthn_challenges'][user_id] = {
        'challenge': challenge,
        'type': 'registration',
    }
    return options_to_json(options)

def register_complete(user_id, credential):
    challenge_data = current_app.config.get('webauthn_challenges', {}).pop(user_id, None)
    if not challenge_data or challenge_data['type'] != 'registration':
        raise ValueError('No pending registration challenge')
    origin = get_origin()
    rp_id = get_rp_id()
    verification = verify_registration_response(
        credential=credential,
        expected_challenge=challenge_data['challenge'],
        expected_rp_id=rp_id,
        expected_origin=origin,
    )
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO webauthn_credentials (user_id, credential_id, public_key, sign_count) VALUES (?, ?, ?, ?)',
        (user_id, verification.credential_id.hex(), verification.credential_public_key.hex(),
         verification.sign_count),
    )
    conn.commit()
    conn.close()
    return {'id': None, 'name': 'Windows Hello'}

def login_begin(username=None):
    conn = get_db_connection()
    if username:
        user = conn.execute('SELECT * FROM usuarios_sistema WHERE username = ?',
                           (username,)).fetchone()
    else:
        user = None
    if user:
        creds = conn.execute('SELECT * FROM webauthn_credentials WHERE user_id = ?',
                            (user['id'],)).fetchall()
    else:
        creds = conn.execute('SELECT * FROM webauthn_credentials').fetchall()
    conn.close()
    if not creds:
        raise ValueError('No credentials registered')
    allow_credentials = [
        {'id': bytes.fromhex(c['credential_id']), 'type': 'public-key'}
        for c in creds
    ]
    challenge = secrets.token_bytes(32)
    options = generate_authentication_options(
        rp_id=get_rp_id(),
        challenge=challenge,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    challenge_id = secrets.token_urlsafe(16)
    if 'webauthn_challenges' not in current_app.config:
        current_app.config['webauthn_challenges'] = {}
    current_app.config['webauthn_challenges'][challenge_id] = {
        'challenge': challenge,
        'type': 'authentication',
        'allow_credentials': [c['credential_id'] for c in creds],
    }
    return options_to_json(options), creds[0]['credential_id'], challenge_id

def login_complete(credential, credential_id_hex, challenge_id):
    challenge_data = current_app.config.get('webauthn_challenges', {}).pop(challenge_id, None)
    if not challenge_data or challenge_data['type'] != 'authentication':
        raise ValueError('No pending authentication challenge')
    conn = get_db_connection()
    cred = conn.execute(
        'SELECT * FROM webauthn_credentials WHERE credential_id = ?',
        (credential_id_hex,),
    ).fetchone()
    if not cred:
        conn.close()
        raise ValueError('Credential not found')
    user = conn.execute('SELECT * FROM usuarios_sistema WHERE id = ?',
                       (cred['user_id'],)).fetchone()
    conn.close()
    if not user:
        raise ValueError('User not found')
    origin = get_origin()
    rp_id = get_rp_id()
    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=challenge_data['challenge'],
        expected_rp_id=rp_id,
        expected_origin=origin,
        credential_public_key=bytes.fromhex(cred['public_key']),
        credential_current_sign_count=cred['sign_count'],
    )
    conn = get_db_connection()
    conn.execute('UPDATE webauthn_credentials SET sign_count = ? WHERE id = ?',
                (verification.new_sign_count, cred['id']))
    conn.commit()
    conn.close()
    return dict(user)
