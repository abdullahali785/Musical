#!/usr/bin/env python3
""" Musical routes """

from datetime import datetime
from flask import Blueprint, current_app, redirect, render_template, request, url_for

view = Blueprint("view", __name__, url_prefix="/view")
edit = Blueprint("edit", __name__, url_prefix="/edit")

from App import db;
from App.models import Production, Students, Role, RoleAssignment, CreativeRole, Adult, CreativeAssignment, Song, SongAssignment

# --- Add Rows ---
def add():
    p = Production(
        title="The Little Mermaid",
        subtitle="Disney's Production",
        image="https://upload.wikimedia.org/wikipedia/en/c/c0/The_Little_Mermaid_%28Official_1989_Film_Poster%29.png",
        start_date=datetime(2025, 12, 10),
        end_date=datetime(2025, 12, 12),
        location="CFL Building, Luther College, Decorah, Iowa",
        price=10.0,
        notes="Photography and Videography are strictly prohibited!",
        thanks="Thank You for your time! We hope you liked our musical.",
        is_active=True
    )
    db.session.add(p)
    db.session.commit()

    r = Role(name="Ariel", production_id=p.id)
    db.session.add(r)
    db.session.commit()

    ra = RoleAssignment(role_id=r.id, student_id=1)
    db.session.add(ra)

    a = Adult(name="Abdullah", production_id=p.id)
    cr = CreativeRole(name="Technology Lead", production_id=p.id)
    db.session.add_all([a, cr])
    db.session.commit()

    ca = CreativeAssignment(role_id=cr.id, adult_id=a.id)
    db.session.add(ca)

    s = Song(title="The World Above", act=1, production_id=p.id)
    db.session.add(s)
    db.session.commit()

    sa = SongAssignment(song_id=s.id, role_id=r.id)
    db.session.add(sa)

    for student_id in [10, 20, 30]:
        student = Students.query.filter_by(id=student_id).first()
        if student:
            student.is_crew = True

    db.session.commit()


# --- View Routes ---

@view.get("/")
def general():
    # add()
    # delete()
    production = Production.query.filter_by(is_active=True).first()
    if not production:
        production = Production.query.first()

    return render_template("view/general.jinja", production=production)

@view.get("/<int:production_id>/cast")
def cast(production_id):
    production = Production.query.get(production_id)
    roles = Role.query.filter_by(production_id=production.id).all()

    return render_template("view/cast.jinja", roles=roles, production=production)

@view.get("/<int:production_id>/team")
def team(production_id):
    crew = Students.query.filter_by(is_crew=True).all()
    team = CreativeAssignment.query.all()

    return render_template("view/team.jinja", crew=crew, team=team)

@view.get("/<int:production_id>/songs")
def songs(production_id):
    song_list = SongAssignment.query.all()
    return render_template("view/songs.jinja", song_list=song_list)
    
@view.get("/<int:production_id>/thanks")
def thanks(production_id):
    production = Production.query.get(production_id)
    return render_template("view/thanks.jinja", production=production)


# --- Edit Routes ---

@edit.get("/all")
def edit_all():
    productions = Production.query.all()
    return render_template("edit/all.jinja", productions=productions)

@edit.post("/all")
def save_all():
    active_id = request.form.get("active_production")
    for prod in Production.query.all():
        prod.is_active = (str(prod.id) == active_id)
    db.session.commit()
    return redirect("/view/")


@edit.get("/<int:production_id>/aspects")
def edit_aspects(production_id):
    return render_template("edit/aspects.jinja", id=production_id)

@edit.get("/new")
def edit_new():
    new_prod = Production(title="Title", subtitle="Sub Title", start_date=None, end_date=None, location="Location", price=0.0, notes="Notes", thanks="Acknowledgments")
    db.session.add(new_prod)
    db.session.commit()

    return redirect(f"/edit/{new_prod.id}/general")


@edit.get("/<int:production_id>/general")
def edit_general(production_id):
    production = Production.query.get(production_id)
    return render_template("edit/general.jinja", production=production)

@edit.post("/<int:production_id>/general")
def save_general(production_id):
    production = Production.query.get_or_404(production_id)

    if request.form.get("delete_production"):
        SongAssignment.query.filter(SongAssignment.song.has(production_id=production.id)).delete(synchronize_session=False)
        Song.query.filter_by(production_id=production.id).delete()
        RoleAssignment.query.filter(RoleAssignment.role.has(production_id=production.id)).delete(synchronize_session=False)
        Role.query.filter_by(production_id=production.id).delete()
        CreativeAssignment.query.filter(CreativeAssignment.role.has(production_id=production.id)).delete(synchronize_session=False)
        CreativeRole.query.filter_by(production_id=production.id).delete()
        Adult.query.filter_by(production_id=production.id).delete()

        db.session.delete(production)
        db.session.commit()
        return redirect("/edit/all")

    production.title = request.form["title"]
    production.subtitle = request.form["subtitle"]
    production.image = request.form["image"]
    production.location = request.form["location"]
    production.price = request.form["price"]
    production.notes = request.form["notes"]
    production.thanks = request.form["thanks"]

    def parse_date(value):
        return datetime.strptime(value, "%Y-%m-%d").date() if value else None
    
    production.start_date = parse_date(request.form["start_date"])
    production.end_date   = parse_date(request.form["end_date"])

    is_active = request.form.get("is_active") == "on"
    production.is_active = is_active

    db.session.commit()
    return redirect("/edit/all")


@edit.get("/<int:production_id>/cast")
def edit_cast(production_id):
    production = Production.query.get(production_id)
    roles = Role.query.filter_by(production_id=production.id).all()
    students = Students.query.filter_by(is_crew=False).all()

    return render_template("edit/cast.jinja", production=production, roles=roles, students=students)

@edit.post("/<int:production_id>/cast")
def save_cast(production_id):
    production = Production.query.get(production_id)
    
    name = request.form.get("new_role_name")
    is_group = request.form.get("new_role_is_group")
    if name:
        new_role = Role(
            name=name,
            is_group=(is_group == "1"),
            production_id=production.id
        )
        db.session.add(new_role)

    delete_id = request.form.get("delete_role")
    if delete_id:
        Role.query.filter_by(id=delete_id).delete()

    roles = Role.query.filter_by(production_id=production.id).all()

    for role in roles:
        new_name = request.form.get(f"role_name_{role.id}")
        if new_name:
            role.name = new_name

        selected_ids = request.form.getlist(f"role_students_{role.id}[]")
        role.students = Students.query.filter(Students.id.in_(selected_ids)).all()

    new_role_students = request.form.getlist("new_role_students[]")
    for s_id in new_role_students:
        assignment = RoleAssignment(role_id=new_role.id, student_id=int(s_id))
        db.session.add(assignment)

    db.session.commit()
    return redirect("/view/cast")


@edit.get("/<int:production_id>/team")
def edit_team(production_id):
    students = Students.query.all()
    roles = CreativeRole.query.filter_by(production_id=production_id).all()
    adults = Adult.query.filter_by(production_id=production_id).all()

    return render_template("edit/team.jinja", production_id=production_id, students=students, roles=roles, adults=adults)

@edit.post("/<int:production_id>/team")
def save_team(production_id):
    roles = CreativeRole.query.filter_by(production_id=production_id).all()

    new_crew_students = request.form.getlist("new_crew_students[]")
    if new_crew_students:
        crew_ids = set(map(int, new_crew_students))
        for student in Students.query.all():
            student.is_crew = True if student.id in crew_ids else False
        db.session.commit()

    new_adult_name = request.form.get("new_adult_name")
    if new_adult_name:
        new_adult = Adult(name=new_adult_name, production_id=production_id)
        db.session.add(new_adult)
        db.session.flush()
        
    new_role_name = request.form.get("new_role_name")
    if new_role_name:
        new_role = CreativeRole(name=new_role_name, production_id=production_id)
        db.session.add(new_role)
        db.session.flush() 

        new_role_adults = request.form.getlist("new_role_adults[]")
        for aid in new_role_adults:
            db.session.add(CreativeAssignment(role_id=new_role.id, adult_id=int(aid)))

    delete_id = request.form.get("delete_role")
    if delete_id:
        role_to_delete = CreativeRole.query.get(int(delete_id))
        if role_to_delete:
            CreativeAssignment.query.filter_by(role_id=role_to_delete.id).delete()
            db.session.delete(role_to_delete)
            
    for role in roles:
        new_name = request.form.get(f"role_name_{role.id}")
        if new_name:
            role.name = new_name
            
        selected_adults = request.form.getlist(f"role_adults_{role.id}[]")
        CreativeAssignment.query.filter_by(role_id=role.id).delete()
        for aid in selected_adults:
            db.session.add(CreativeAssignment(role_id=role.id, adult_id=int(aid)))

    db.session.commit()
    return redirect(f"/view/team")


@edit.get("/<int:production_id>/songs")
def edit_songs(production_id):
    production = Production.query.get(production_id)
    songs = Song.query.filter_by(production_id=production_id).all()
    roles = Role.query.filter_by(production_id=production_id).all()

    return render_template("edit/songs.jinja", production=production, songs=songs, roles=roles)

@edit.post("/<int:production_id>/songs")
def save_songs(production_id):
    with db.session.no_autoflush:
        new_song_title = request.form.get("new_song_title")
        if new_song_title:
            raw_act = request.form.get("new_song_act")
            new_song_act = int(raw_act) if raw_act and raw_act.isdigit() else 10
            new_song_msg = request.form.get("new_song_intermission_message", "")

            new_song = Song(
                title=new_song_title,
                act=new_song_act,
                intermission_message=new_song_msg,
                production_id=production_id
            )
            db.session.add(new_song)
            db.session.commit()
            db.session.flush()

            assigned_roles = request.form.getlist("new_song_roles[]")
            for r_id in assigned_roles:
                db.session.add(SongAssignment(song_id=new_song.id, role_id=int(r_id)))

        delete_id = request.form.get("delete_song")
        if delete_id:
            SongAssignment.query.filter_by(song_id=int(delete_id)).delete(synchronize_session=False)
            song_to_delete = Song.query.get(int(delete_id))
            if song_to_delete:
                db.session.delete(song_to_delete)
                db.session.commit()
                
        songs = Song.query.filter_by(production_id=production_id).all()
        for song in songs:
            title = request.form.get(f"song_title_{song.id}")
            if title:
                song.title = title

                raw_act = request.form.get(f"song_act_{song.id}")
                if raw_act is None or raw_act.strip() == "":
                    song.act = 20
                else:
                    song.act = int(raw_act)

                msg = request.form.get(f"song_msg_{song.id}")
                song.intermission_message = msg or ""

                selected_roles = request.form.getlist(f"song_roles_{song.id}[]")
                SongAssignment.query.filter_by(song_id=song.id).delete()
                for rid in selected_roles:
                    db.session.add(SongAssignment(song_id=song.id, role_id=int(rid)))

    db.session.commit()
    return redirect(f"/view/songs")


@edit.get("/<int:production_id>/thanks")
def edit_thanks(production_id):
    production = Production.query.get(production_id)
    return render_template("edit/thanks.jinja", production=production)

@edit.post("/<int:production_id>/thanks")
def save_thanks(production_id):
    production = Production.query.get(production_id)
    production.thanks = request.form.get("thanks_text", "")
    db.session.commit()
    return redirect(f"/view/thanks")