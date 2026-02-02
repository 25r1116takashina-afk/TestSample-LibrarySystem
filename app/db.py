import sqlite3
import click
from flask import current_app, g

def get_db():
    """データベース接続を取得します。"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    """データベース接続を閉じます。"""
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    """初期設定：SQLファイルからテーブルを作成します。"""
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    """既存データを削除し、新しいテーブルを作成します。"""
    init_db()
    click.echo('データベースを初期化しました。')

def init_app(app):
    """FlaskアプリにDB関連の関数を登録します。"""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
