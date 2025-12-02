#!/usr/bin/env python3
""" Musical Database """

import csv, datetime, logging, pathlib, click
import sqlalchemy as sqla
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import (
    DeclarativeBase,
    backref,
    relationship,
    scoped_session,
    sessionmaker,
)

# db = SQLAlchemy()
from App import db;

# --- Production ---

class Production(db.Model):
    __tablename__ = "production"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    subtitle = Column(String)
    image = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    location = Column(String)
    price = Column(Float)
    notes = Column(String)
    thanks = Column(String)
    is_active = Column(Boolean)

    def __repr__(self):
        return f"Production Title({self.title})"
    

# --- Students and Cast ---

class Students(db.Model):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    sex = Column(String(1))
    year = Column(String(15))
    is_crew = Column(Boolean, default=False)

    roles = relationship("Role", secondary="role_assignment", back_populates="students")

    def __repr__(self):
        return f"Student({self.name})"
    
class Role(db.Model):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String)
    production_id = Column(Integer, ForeignKey("production.id"))
    is_group = Column(Boolean, default=False)

    students = relationship("Students", secondary="role_assignment", back_populates="roles")
    songs = relationship("Song", secondary="song_assignment", back_populates="singers")

    def __repr__(self):
        return f"Role({self.name})"
    
class RoleAssignment(db.Model):
    __tablename__ = "role_assignment"

    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), primary_key=True)

    role = relationship("Role", backref="assignments")
    student = relationship("Students", backref="roles_played")

    def __repr__(self):
        return f"Role-ID ({self.role_id}), Student-ID ({self.student_id})"


# --- Adults and Creative Team ---

class CreativeRole(db.Model):
    __tablename__ = "creative_role"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    production_id = Column(Integer, ForeignKey("production.id"))

    adults = relationship("Adult", secondary="creative_assignment", back_populates="roles")

    def __repr__(self):
        return f"Creative Role ({self.name})"

class Adult(db.Model):
    __tablename__ = "adult"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    production_id = Column(Integer, ForeignKey("production.id"))

    roles = relationship("CreativeRole", secondary="creative_assignment", back_populates="adults")

    def __repr__(self):
        return f"Adult ({self.name})"

class CreativeAssignment(db.Model):
    __tablename__ = "creative_assignment"

    role_id = Column(Integer, ForeignKey("creative_role.id"), primary_key=True)
    adult_id = Column(Integer, ForeignKey("adult.id"), primary_key=True)

    role = relationship("CreativeRole")
    adult = relationship("Adult")

    def __repr__(self):
        return f"Creative-Role-ID ({self.role_id}), Adult-ID ({self.adult_id})"


# --- Songs ---

class Song(db.Model):
    __tablename__ = "song"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    act = Column(Integer)
    intermission_message = Column(String, default="")
    production_id = Column(Integer, ForeignKey("production.id"))

    production = relationship("Production", backref="songs")
    singers = relationship("Role", secondary="song_assignment", back_populates="songs")

    def __repr__(self):
        return f"Song({self.title}, Order {self.order})"

class SongAssignment(db.Model):
    __tablename__ = "song_assignment"

    song_id = Column(Integer, ForeignKey("song.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True)

    role = relationship("Role")
    song = relationship("Song")

    def __repr__(self):
        return f"Song-ID ({self.song_id}), Role-ID ({self.role_id})"


# --- End ---

def create_db(app):
    """Create database directly (no CLI needed)"""
    from . import Students
    import pathlib, csv

    db_file = app.config.get("SQLALCHEMY_DATABASE_URI").replace("sqlite:///", "")
    db_path = pathlib.Path(db_file)

    # Delete existing DB
    if db_path.exists():
        db_path.unlink()

    # Wrap DB creation and session in app context
    with app.app_context():
        # Build tables
        db.create_all()

        # Add initial data from CSV
        session = db.session
        this_dir = pathlib.Path(__file__).parent
        data_file = this_dir.parent / "Data" / "cast.csv"
        with open(data_file, "r", encoding="utf8") as f:
            content = csv.DictReader(f)
            for item in content:
                student = Students(
                    name=item["name"],
                    sex=item["sex"],
                    year=item["year"]
                )
                session.add(student)
            session.commit()

    print("Database created successfully.")


@click.command(help="Create a database from the CSV file")
@click.pass_context
def create(ctx) -> None:
    """Create database"""
    engine = ctx.obj["engine"]
    session = ctx.obj["session"]
    filename = ctx.obj["filename"]

    # Delete existing DB
    if pathlib.Path(f"{filename}.sqlite3").exists():
        pathlib.Path(f"{filename}.sqlite3").unlink()

    # Build tables
    db.metadata.create_all(engine)

    # Add data
    this_dir = pathlib.Path(__file__).parent
    data_file = this_dir.parent / "Data" / "cast.csv"
    with open(data_file, "r", encoding="utf8") as f:
        content = csv.DictReader(f, delimiter=",")
        for item in content:
            student = Students(
                name = item["name"],
                sex = item["sex"],
                year = item["year"],
            )
            session.add(student)
        session.commit()

    print("Database created successfully.")


@click.command(help="Read all records from the database")
@click.pass_context
def read(ctx) -> None:
    """Read all records"""
    session = ctx.obj["session"]
    print(f"{'name':10s}{'sex':10s}{'year':10s}")

    students = session.query(Students).all()
    for s in students:
        print(f"{s.name:10s}{s.sex:10s}{s.year:10s}")


@click.group()
@click.option("--verbose", "-v", is_flag=True, default=False)
@click.argument("filename")
@click.pass_context
def cli(ctx, verbose: bool, filename: str) -> None:
    """Command-line interface"""
    ctx.ensure_object(dict)
    if verbose:
        logging.basicConfig(level=logging.INFO)

    this_dir = pathlib.Path(__file__).parent
    data_dir = this_dir.parent / "Data"

    engine = sqla.create_engine(f"sqlite:////{data_dir}/{filename}.sqlite3")
    session = scoped_session(sessionmaker(bind=engine))

    ctx.obj["session"] = session
    ctx.obj["engine"] = engine
    ctx.obj["filename"] = filename

def main():
    """Main function"""
    cli.add_command(create)
    cli.add_command(read)
    cli()

if __name__ == "__main__":
    main()