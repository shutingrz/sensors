from flask import Flask, Blueprint
from app.controllers.api import api
from app.controllers.webui import webui
from app.util import Util
from flask_wtf.csrf import CSRFProtect
from app import db
from flask_sqlalchemy import SQLAlchemy

def create_app(DBURL=None):

    app = Flask(__name__)

    try:
        app.config.from_pyfile('../sensors.conf')
    except FileNotFoundError as exc:
        app.logger.critical("'../sensors.conf' is not found.")
        raise FileNotFoundError(exc)

    try:
        if DBURL is not None:
            dburl = DBURL
        else:
            dburl = app.config['DBURL']

        app.config['SQLALCHEMY_DATABASE_URI'] = dburl
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    except KeyError as exc:
        app.logger.critical(
            "DBURL is not set. please set dburl at sensors.conf!")
        raise KeyError(exc)

    app.config["SECRET_KEY"] = Util.generateRandomBytes(32)
    app.config['JSON_AS_ASCII'] = False

    Util.MaxUsernameLength = app.config["MAX_USERID_LENGTH"]
    Util.MaxUserPassLength = app.config["MAX_USERPASS_LENGTH"]

    csrf = CSRFProtect(app)
    csrf.init_app(app)

    # ビューの登録
    app.register_blueprint(webui, url_prefix='/')
    app.register_blueprint(api, url_prefix='/api/')

    # データベースの登録
    db.init_db(app)

    return app


app = create_app()

# Migrate対応だが一旦 db.create_all() をする運用とする
with app.app_context():
	db.create_all()
