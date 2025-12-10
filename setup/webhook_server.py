#!/usr/bin/env python3
"""
Stock Analyzer デプロイ用 Webhook サーバー

このサーバーはGitHubのWebhookイベント（タグのpushとリリース）を受け取り、
指定されたバージョンをRaspberry Piに自動デプロイします。
"""
import hmac
import hashlib
import json
import subprocess
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# 設定
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', '')
REPO_PATH = os.environ.get('REPO_PATH', os.path.expanduser('~/stock_analyzer'))
COMPOSE_FILE = 'docker-compose.prod.yml'
LOG_FILE = os.path.expanduser('~/logs/deploy.log')

def log_message(message):
    """タイムスタンプ付きでログメッセージを記録"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry, end='')
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"ログファイルへの書き込みに失敗: {e}")

class WebhookHandler(BaseHTTPRequestHandler):
    def verify_signature(self, payload, signature):
        """GitHub Webhookの署名を検証"""
        if not signature:
            log_message("ERROR: 署名が提供されていません")
            return False

        if not WEBHOOK_SECRET:
            log_message("ERROR: WEBHOOK_SECRETが設定されていません")
            return False

        try:
            sha_name, signature_hash = signature.split('=')
            if sha_name != 'sha256':
                log_message(f"ERROR: サポートされていないハッシュアルゴリズム: {sha_name}")
                return False

            mac = hmac.new(
                WEBHOOK_SECRET.encode(),
                msg=payload,
                digestmod=hashlib.sha256
            )
            is_valid = hmac.compare_digest(mac.hexdigest(), signature_hash)

            if not is_valid:
                log_message("ERROR: 署名が無効です")

            return is_valid
        except Exception as e:
            log_message(f"ERROR: 署名検証に失敗: {e}")
            return False

    def deploy_tag(self, tag_name):
        """指定されたタグをデプロイ"""
        log_message(f"タグのデプロイを開始: {tag_name}")

        try:
            # リポジトリディレクトリに移動
            os.chdir(REPO_PATH)
            log_message(f"ディレクトリを変更: {REPO_PATH}")

            # Gitタグを取得
            log_message("リモートからタグを取得中...")
            result = subprocess.run(
                ['git', 'fetch', '--tags'],
                capture_output=True,
                text=True,
                check=True
            )
            log_message(f"Git fetch 出力: {result.stdout}")

            # 指定されたタグにチェックアウト
            log_message(f"タグをチェックアウト: {tag_name}")
            result = subprocess.run(
                ['git', 'checkout', tag_name],
                capture_output=True,
                text=True,
                check=True
            )
            log_message(f"Git checkout 出力: {result.stdout}")

            # 既存のコンテナを停止
            log_message("既存のコンテナを停止中...")
            result = subprocess.run(
                ['docker', 'compose', '-f', COMPOSE_FILE, 'down'],
                capture_output=True,
                text=True,
                check=True
            )
            log_message(f"Docker down 出力: {result.stdout}")

            # コンテナをビルドして起動
            log_message("コンテナをビルドして起動中...")
            result = subprocess.run(
                ['docker', 'compose', '-f', COMPOSE_FILE, 'up', '-d', '--build'],
                capture_output=True,
                text=True,
                check=True
            )
            log_message(f"Docker up 出力: {result.stdout}")

            log_message(f"✓ {tag_name} のデプロイに成功しました")
            return True, f"Successfully deployed {tag_name}"

        except subprocess.CalledProcessError as e:
            error_msg = f"コマンド実行失敗: {e.cmd}\nリターンコード: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            log_message(f"ERROR: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"予期しないエラー: {str(e)}"
            log_message(f"ERROR: {error_msg}")
            return False, error_msg

    def do_POST(self):
        """POSTリクエストを処理"""
        if self.path != '/webhook':
            self.send_response(404)
            self.end_headers()
            return

        # リクエストボディを読み取り
        content_length = int(self.headers['Content-Length'])
        payload = self.rfile.read(content_length)

        # 署名を検証
        signature = self.headers.get('X-Hub-Signature-256')
        if not self.verify_signature(payload, signature):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Invalid signature')
            return

        # JSONをパース
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            log_message(f"ERROR: 無効なJSON: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON')
            return

        # イベントタイプを取得
        event_type = self.headers.get('X-GitHub-Event')
        log_message(f"Webhookを受信: {event_type}")

        tag_name = None

        # タグpushイベント
        if event_type == 'push' and data.get('ref', '').startswith('refs/tags/'):
            tag_name = data['ref'].replace('refs/tags/', '')
            log_message(f"タグpushを検知: {tag_name}")

        # リリースイベント
        elif event_type == 'release':
            action = data.get('action')
            if action == 'published':
                tag_name = data.get('release', {}).get('tag_name')
                log_message(f"リリースが公開されました: {tag_name}")
            else:
                log_message(f"リリースアクション '{action}' は無視されました")

        if not tag_name:
            log_message("イベントを無視 (デプロイ可能なタグが見つかりません)")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Event ignored')
            return

        # デプロイを実行
        success, message = self.deploy_tag(tag_name)

        if success:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(message.encode())
        else:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Deployment failed: {message}'.encode())

    def do_GET(self):
        """GETリクエストを処理（ヘルスチェック）"""
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """デフォルトのログフォーマットをオーバーライド"""
        log_message(f"{self.address_string()} - {format % args}")

def run_server(port=9000):
    """Webhookサーバーを起動"""
    if not WEBHOOK_SECRET:
        print("ERROR: WEBHOOK_SECRET 環境変数が設定されていません！")
        print("サーバーを起動する前に設定してください:")
        print("  export WEBHOOK_SECRET='your-secret-here'")
        sys.exit(1)

    log_message(f"Webhookサーバーを起動中（ポート {port}）...")
    log_message(f"リポジトリパス: {REPO_PATH}")
    log_message(f"Composeファイル: {COMPOSE_FILE}")
    log_message(f"ログファイル: {LOG_FILE}")

    try:
        server = HTTPServer(('0.0.0.0', port), WebhookHandler)
        log_message(f"✓ Webhookサーバーがポート {port} で稼働中")
        server.serve_forever()
    except KeyboardInterrupt:
        log_message("サーバーがユーザーによって停止されました")
    except Exception as e:
        log_message(f"ERROR: サーバーの起動に失敗: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_server()
