from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required, admin_required
from app.db import get_db

bp = Blueprint('books', __name__, url_prefix='/books')

@bp.route('/')
def index():
    db = get_db()
    query = request.args.get('q', '')
    
    sql = 'SELECT * FROM book WHERE is_deleted = 0'
    params = []

    if query:
        # 【正常版】タイトル、ISBN、著者名で部分一致検索（安全な入力処理）
        # 【バグ版：feature/buggy-version では以下のように記述されています】
        # if "'" in query or "%" in query:
        #     raise Exception("データベースエラー: SQL構文エラーが発生しました。")
        
        sql += ' AND (title LIKE ? OR isbn LIKE ? OR author LIKE ?)'
        search_term = f'%{query}%'
        params = [search_term, search_term, search_term]
    
    sql += ' ORDER BY id DESC'
    
    books = db.execute(sql, params).fetchall()
    return render_template('books/index.html', books=books, query=query)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
@admin_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        isbn = request.form['isbn']
        author = request.form['author']
        publisher = request.form['publisher']
        stock_count = request.form['stock_count']
        error = None

        if not title:
            error = 'タイトルは必須です。'
        elif not isbn:
            error = 'ISBNは必須です。'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO book (title, isbn, author, publisher, stock_count) VALUES (?, ?, ?, ?, ?)',
                (title, isbn, author, publisher, stock_count)
            )
            db.commit()
            return redirect(url_for('books.index'))

    return render_template('books/create.html')

def get_book(id):
    """IDに一致する書籍を取得します（削除されていないもののみ）。"""
    book = get_db().execute(
        'SELECT * FROM book WHERE id = ? AND is_deleted = 0',
        (id,)
    ).fetchone()

    if book is None:
        abort(404, f"書籍ID {id} は存在しません。")

    return book

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
@admin_required
def update(id):
    book = get_book(id)

    if request.method == 'POST':
        title = request.form['title']
        isbn = request.form['isbn']
        author = request.form['author']
        publisher = request.form['publisher']
        stock_count = request.form['stock_count']
        error = None

        if not title:
            error = 'タイトルは必須です。'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE book SET title = ?, isbn = ?, author = ?, publisher = ?, stock_count = ?'
                ' WHERE id = ?',
                (title, isbn, author, publisher, stock_count, id)
            )
            db.commit()
            return redirect(url_for('books.index'))

    return render_template('books/update.html', book=book)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
@admin_required
def delete(id):
    db = get_db()
    
    # 【正常版】削除前に貸出中の件数を確認し、貸出中なら削除をブロックする
    # 【バグ版：feature/buggy-version ではこのチェックがありません】
    active_loan = db.execute(
        'SELECT id FROM loan WHERE book_id = ? AND return_date IS NULL',
        (id,)
    ).fetchone()
    
    if active_loan:
        flash("削除できません: 貸出中のため削除できません。")
        return redirect(url_for('books.index'))

    # 【正常版】論理削除（is_deletedフラグを立てる）
    # 【バグ版：feature/buggy-version では DELETE FROM book WHERE id = ? で物理削除しています】
    db.execute('UPDATE book SET is_deleted = 1 WHERE id = ?', (id,))
    
    # 注意: 貸出履歴データは保持されます。
    
    db.commit()
    return redirect(url_for('books.index'))
