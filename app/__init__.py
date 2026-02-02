import os

from flask import Flask, render_template

def create_app(test_config=None):
    # アプリ作成と設定
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'library.sqlite'),
    )

    if test_config is None:
        # テスト時以外は、設定ファイル (config.py) を読み込む
        app.config.from_pyfile('config.py', silent=True)
    else:
        # テスト時は、引数で渡された設定を読み込む
        app.config.from_mapping(test_config)

    # インスタンスフォルダ（DB保存先）の作成
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # DBの初期化設定
    from . import db
    db.init_app(app)

    # 各機能のBlueprintを登録
    from . import auth
    app.register_blueprint(auth.bp)

    from . import books
    app.register_blueprint(books.bp)
    
    from . import loans
    app.register_blueprint(loans.bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app
