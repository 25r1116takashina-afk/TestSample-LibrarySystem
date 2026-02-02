import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import abort

from app.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# --- 認証関連のビュー ---

@bp.route('/login', methods=('GET', 'POST'))
def login():
    """ログイン処理を行います。"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        
        # ユーザーの取得
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        # バリデーションチェック
        if user is None:
            error = 'ユーザー名が正しくありません。'
        elif not check_password_hash(user['password'], password):
            error = 'パスワードが正しくありません。'

        if error is None:
            # セッションにユーザーIDを保存
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    """リクエストの前にログインユーザーの情報をロードします。"""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    """ログアウト処理：セッションをクリアしてログイン画面へ戻ります。"""
    session.clear()
    return redirect(url_for('auth.login'))

# --- デコレーター (アクセス制御) ---

def login_required(view):
    """ログインが必要なページへのアクセスを制限するデコレーターです。"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

def admin_required(view):
    """管理者権限が必要なページへのアクセスを制限するデコレーターです。"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        if g.user['role'] != 'admin':
            abort(403) # 権限なし(Forbidden)

        return view(**kwargs)

    return wrapped_view
