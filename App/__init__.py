#!/usr/bin/env python3
""" Musical initialization """

import pathlib, dotenv
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app() -> Flask:
    from App.routes import view, edit

    this_app = Flask(__name__)
    with this_app.app_context():
        this_dir = pathlib.Path(__file__).parent

        dotenv.load_dotenv(this_dir / pathlib.Path(".flaskenv"))
        this_app.config.from_prefixed_env()

    
        this_app.config['PATH_DATA_FILE'] = this_dir.parent / "data" / pathlib.Path(f"{this_app.config['DATA_FILE']}.sqlite3")
        db_file = this_app.config['PATH_DATA_FILE']

        this_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:////{db_file}"
        db.init_app(this_app)
            
        this_app.register_blueprint(view, url_prefix="/view") 
        this_app.register_blueprint(edit, url_prefix="/edit") 

        @this_app.route("/")
        def root_redirect():
            return redirect("/view/")

    return this_app