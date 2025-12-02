#!/usr/bin/env python3
""" Musical initialization """

import os, pathlib, dotenv, subprocess
from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app() -> Flask:
    from App.routes import view, edit
    from App.models import create_db

    this_app = Flask(__name__)
    this_dir = pathlib.Path(__file__).parent

    with this_app.app_context():
        if os.environ.get("RENDER") is None:
            dotenv.load_dotenv(this_dir / ".flaskenv")
        this_app.config.from_prefixed_env()

        data_file = this_app.config.get("DATA_FILE", "cast") + ".sqlite3"
        if os.environ.get("RENDER"):
            db_path = pathlib.Path("/opt/render/project/src/tmp") / data_file
        else:
            db_path = this_dir.parent / "data" / data_file

        db_path.parent.mkdir(parents=True, exist_ok=True)

        this_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        this_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        db.init_app(this_app)
        if not db_path.exists():
            print("DB not found — creating...")
            create_db()

        this_app.register_blueprint(view, url_prefix="/view")
        this_app.register_blueprint(edit, url_prefix="/edit")

        @this_app.route("/")
        def root_redirect():
            return redirect("/view/")

    return this_app