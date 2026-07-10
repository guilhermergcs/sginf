import secrets
import threading
import logging
from datetime import datetime, timedelta, timezone
from flask import current_app
from app.db import get_db_connection

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def generate_token():
    return secrets.token_urlsafe(32)

def create_auth_token(purpose, user_id=None):
    token = generate_token()
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO auth_tokens (token, user_id, purpose, expires_at) VALUES (?, ?, ?, ?)',
        (token, user_id, purpose, datetime.now(timezone.utc) + timedelta(minutes=5)),
    )
    conn.commit()
    conn.close()
    return token

def check_token(token):
    conn = get_db_connection()
    t = conn.execute(
        'SELECT * FROM auth_tokens WHERE token = ? AND consumed = 0 AND expires_at > ?',
        (token, datetime.now(timezone.utc)),
    ).fetchone()
    conn.close()
    return dict(t) if t else None

def consume_token(token, telegram_chat_id):
    conn = get_db_connection()
    conn.execute(
        'UPDATE auth_tokens SET consumed = 1, telegram_chat_id = ? WHERE token = ?',
        (telegram_chat_id, token),
    )
    conn.commit()
    conn.close()

def link_telegram(user_id, telegram_chat_id):
    conn = get_db_connection()
    conn.execute(
        'UPDATE usuarios_sistema SET telegram_id = ?, telegram_linked = 1 WHERE id = ?',
        (telegram_chat_id, user_id),
    )
    conn.commit()
    conn.close()

def get_user_by_telegram(telegram_chat_id):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM usuarios_sistema WHERE telegram_id = ?',
        (telegram_chat_id,),
    ).fetchone()
    conn.close()
    return dict(user) if user else None

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self._thread = None
        self._stop = threading.Event()

    def start(self, app):
        if not self.token:
            log.warning('TELEGRAM_BOT_TOKEN not set, bot disabled')
            return
        def run():
            import asyncio
            from telegram import Update
            from telegram.ext import Application, CommandHandler, ContextTypes

            application = Application.builder().token(self.token).build()

            async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                await update.message.reply_text(
                    'Bot do SGINF\n\n'
                    '/login <codigo> - Entrar no sistema\n'
                    '/link <codigo> - Vincular Telegram a sua conta\n\n'
                    'Gere um codigo na pagina de login ou ajustes.'
                )

            async def login_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if not context.args:
                    await update.message.reply_text('Use: /login <codigo>')
                    return
                token = context.args[0]
                t = check_token(token)
                if not t:
                    await update.message.reply_text('Codigo invalido ou expirado.')
                    return
                if t['purpose'] != 'telegram_login':
                    await update.message.reply_text('Codigo invalido para login.')
                    return
                user = get_user_by_telegram(update.effective_chat.id)
                if not user:
                    await update.message.reply_text(
                        'Sua conta do Telegram nao esta vinculada a nenhum usuario. '
                        'Vincule primeiro em Ajustes > Telegram usando /link.'
                    )
                    return
                consume_token(token, update.effective_chat.id)
                await update.message.reply_text('Login autorizado! Volte ao navegador.')

            async def link_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if not context.args:
                    await update.message.reply_text('Use: /link <codigo>')
                    return
                token = context.args[0]
                t = check_token(token)
                if not t:
                    await update.message.reply_text('Codigo invalido ou expirado.')
                    return
                if t['purpose'] != 'telegram_link' or not t['user_id']:
                    await update.message.reply_text('Codigo invalido para vinculacao.')
                    return
                consume_token(token, update.effective_chat.id)
                link_telegram(t['user_id'], update.effective_chat.id)
                await update.message.reply_text(
                    'Telegram vinculado com sucesso! Agora voce pode fazer login com /login.'
                )

            application.add_handler(CommandHandler('start', start_cmd))
            application.add_handler(CommandHandler('login', login_cmd))
            application.add_handler(CommandHandler('link', link_cmd))

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.start())
            log.info('Telegram bot started polling')
            loop.run_until_complete(application.updater.start_polling())
            self._stop.wait()
            loop.run_until_complete(application.updater.stop())
            loop.run_until_complete(application.stop())
            loop.run_until_complete(application.shutdown())

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
