from flask import Flask, request, jsonify, redirect, url_for, render_template, flash,current_app
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from sqlalchemy import func

# ---------- use models.py (single source of truth) ----------
# Make sure models.py defines: db, User, VocationalTrack, TrainingCentre, Career (if needed), CentreCourse (if needed)
from models import db, User, VocationalTrack, TrainingCentre, CentreCourse

app = Flask(__name__)
CORS(app, supports_credentials=True)

# --- Add a secret key for session management ---
app.config['SECRET_KEY'] = os.urandom(24)

db_uri = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:23562@localhost:5432/VocationalUdaan"
)

# --- DATABASE CONFIGURATION ---
db_uri = "postgresql://postgres:23562@localhost:5432/VocationalUdaan"
#db_uri="postgresql://neondb_owner:npg_vWE5oT3FhZAp@ep-plain-pond-a116bs24-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# IMPORTANT: initialize the imported db with the app (do NOT create a new SQLAlchemy instance)
db.init_app(app)

# --- LOGIN MANAGER SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "index"  # change if you have a dedicated login page

# --- Routes -----------------------------------------------------------------

@app.route('/')
def index():
    # Renders templates/index.html (your front page)
    return render_template('index.html')


@login_manager.user_loader
def load_user(user_id: str):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

def _is_api_request(req):
    # treat fetch/json and XHR as API
    return req.is_json or req.headers.get("X-Requested-With") == "XMLHttpRequest" \
           or "application/json" in (req.headers.get("Accept", "") or "")

# @app.route('/signup', methods=['POST'])
# def signup_user():
#     data = request.json or request.form or {}
#     # required fields check (works for both fetch/json and plain form)
#     if not all(k in data for k in ['name', 'email', 'phone_number', 'password']):
#         if request.is_json:
#             return jsonify({'error': 'Name, email, phone_number and password are required.'}), 400
#         flash("Please provide name, email, phone and password", "error")
#         return redirect(url_for('index'))

#     # duplicate check
#     if User.query.filter_by(email=data['email']).first():
#         if request.is_json:
#             return jsonify({'error': 'A user with this email already exists.'}), 409
#         flash("A user with this email already exists!", "error")
#         # redirect to login page so user can sign in instead
#         return redirect(url_for('index'))   # <-- browser redir to login page

#     # create user
#     new_user = User(
#         name=data['name'],
#         email=data['email'],
#         phone_number=data['phone_number'],
#         education=data.get('education')
#     )
#     # set password if method exists on model, else set hashed field
#     if hasattr(new_user, 'set_password'):
#         new_user.set_password(data['password'])
#     else:
#         new_user.password_hash = generate_password_hash(data['password'])

#     db.session.add(new_user)
#     db.session.commit()

#     # After signup we DO NOT auto-login (you asked to redirect to login).
#     if request.is_json:
#         # tell frontend to redirect to login page
#         return jsonify({'message': 'User created. Please login.', 'redirect': url_for('index')}), 201

#     flash("Account created — please login.", "success")
#     return redirect(url_for('index'))   # browser -> show login page


# # ------------------ Login route (serve page on GET, handle auth on POST) ------------------
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     # GET: render login page (form)
#     if request.method == 'GET':
#         return render_template('login.html')   # <-- make sure templates/login.html exists

#     # POST: attempt authentication
#     data = request.json or request.form or {}
#     email = data.get('email')
#     pwd = data.get('password')

#     if not email or not pwd:
#         if request.is_json:
#             return jsonify({'error': 'email and password required'}), 400
#         flash("Email and password required", "error")
#         return redirect(url_for('login'))

#     user = User.query.filter_by(email=email).first()
#     # use your model's check_password if present
#     if user and getattr(user, 'check_password', None) and user.check_password(pwd):
#         login_user(user)
#         if request.is_json:
#             return jsonify({'message': 'Logged in successfully.', 'redirect': url_for('search')}), 200
#         # browser login -> redirect to search page
#         return redirect(url_for('search'))

#     # invalid credentials
#     if request.is_json:
#         return jsonify({'error': 'Invalid email or password.'}), 401
#     flash("Invalid email or password.", "error")
#     return redirect(url_for('login'))

@app.route('/signup', methods=['POST'])
def signup_user():
    data = request.json or request.form or {}
    # require fields
    if not all(k in data and data[k] for k in ['name', 'email', 'phone_number', 'password']):
        if request.is_json:
            return jsonify({'error': 'Name, email, phone_number and password are required.'}), 400
        flash("Please provide name, email, phone and password", "error")
        return redirect(url_for('index'))

    # normalize email for consistent storage
    email = data['email'].strip().lower()

    existing = User.query.filter(func.lower(User.email) == email).first()
    if existing:
        # If user exists but has no password_hash, ask them to set/reset the password
        if not getattr(existing, "password_hash", None):
            if request.is_json:
                return jsonify({'error': 'Account exists but no password set. Please set your password (use Reset).'}), 409
            flash("Account exists but no password set. Please reset your password.", "error")
            return redirect(url_for('index'))
        # normal duplicate case
        if request.is_json:
            return jsonify({'error': 'A user with this email already exists.'}), 409
        flash("A user with this email already exists!", "error")
        return redirect(url_for('index'))

    # create user and hash password
    new_user = User(
        name=data['name'],
        email=email,
        phone_number=data['phone_number'],
        education=data.get('education')
    )
    if hasattr(new_user, 'set_password'):
        new_user.set_password(data['password'])
    else:
        new_user.password_hash = generate_password_hash(data['password'])

    db.session.add(new_user)
    db.session.commit()

    # After signup redirect to login page (you said you wanted that)
    if request.is_json:
        return jsonify({'message': 'User created. Please login.', 'redirect': url_for('index')}), 201
    flash("Account created — please login.", "success")
    return redirect(url_for('index'))


# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json or request.form or {}
    email = (data.get('email') or "").strip().lower()
    pwd = data.get('password')

    if not email or not pwd:
        if request.is_json:
            return jsonify({'error': 'email and password required'}), 400
        flash("Email and password required", "error")
        return redirect(url_for('index'))

    # case-insensitive lookup
    user = User.query.filter(func.lower(User.email) == email).first()

    if not user:
        if request.is_json:
            return jsonify({'error': 'Invalid email or password.'}), 401
        flash("Invalid email or password.", "error")
        return redirect(url_for('index'))

    # If user exists but has no password hash, give a helpful message
    if not getattr(user, 'password_hash', None):
        # Don't auto-login — ask user to reset password.
        msg = "This account has no password set. Please use password reset or contact admin."
        if request.is_json:
            return jsonify({'error': msg}), 403
        flash(msg, "error")
        return redirect(url_for('index'))

    # finally check password
    if getattr(user, 'check_password', None) and user.check_password(pwd):
        login_user(user)
        if request.is_json:
            return jsonify({'message': 'Logged in successfully.', 'redirect': url_for('search')}), 200
        return redirect(url_for('search'))

    # invalid credentials
    if request.is_json:
        return jsonify({'error': 'Invalid email or password.'}), 401
    flash("Invalid email or password.", "error")
    return redirect(url_for('index'))


# ------------------ route to serve search.html ------------------
@app.route('/search',methods=['GET'])
def search():
    # your template is templates/search.html — render it:
    return render_template('search.html')

@app.route('/search.html')
def search_html():
    return render_template('search.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully.'}), 200


@app.route('/check_auth', methods=['GET'])
def check_auth():
    if current_user.is_authenticated:
        return jsonify({'is_authenticated': True, 'user': {'name': current_user.name}})
    return jsonify({'is_authenticated': False})


# --- Data endpoints ---------------------------------------------------------
@app.route('/sectors', methods=['GET'])
def get_all_sectors():
    # returns list of distinct sectors from careers table
    query_result = db.session.query(VocationalTrack.sector).distinct().filter(VocationalTrack.sector.isnot(None)).order_by(VocationalTrack.sector).all()
    sector_list = [item[0] for item in query_result]
    return jsonify(sector_list)


@app.route('/career/<string:name>', methods=['GET'])
def get_career_details(name):
    career = VocationalTrack.query.filter_by(name=name).first_or_404()
    return jsonify({
        'name': career.name,
        'sector': career.sector,
        'attributes': getattr(career, 'attributes', None),
        'key_learnings': getattr(career, 'key_learnings', None)
    })

@app.route('/match', methods=['POST'])
def match_user():
    data = request.json or {}
    selected_sectors = data.get('sectors', [])
    location = data.get('location', '')

    if not selected_sectors:
        return jsonify({'error': 'Please select at least one sector.'}), 400

    # centres ⟂ centre_courses ⟂ careers(VocationalTrack)
    q = (
        db.session.query(TrainingCentre)
        .join(CentreCourse, CentreCourse.centre_id == TrainingCentre.id)
        .join(VocationalTrack, VocationalTrack.id == CentreCourse.career_id)
        .filter(VocationalTrack.sector.in_(selected_sectors))
    )
    if location:
        q = q.filter(TrainingCentre.address.ilike(f"%{location}%"))

    centres = q.distinct().all()

    results = []
    for centre in centres:
        # courses from this centre that belong to selected sectors
        course_rows = (
            db.session.query(VocationalTrack.name)
            .join(CentreCourse, CentreCourse.career_id == VocationalTrack.id)
            .filter(
                CentreCourse.centre_id == centre.id,
                VocationalTrack.sector.in_(selected_sectors),
            )
            .all()
        )
        offered_courses = [r[0] for r in course_rows]

        # source_url is an ARRAY(Text) in your model; pick first if present
        src = None
        try:
            val = getattr(centre, "source_url", None)
            if isinstance(val, (list, tuple)) and val:
                src = val[0]
            elif isinstance(val, str):
                src = val
        except Exception:
            pass

        results.append({
            "centre_name": centre.name,
            "address": centre.address,
            "contact": getattr(centre, "contact", None),
            "source_url": src,
            "offered_courses": offered_courses,
        })

    return jsonify(results)


# --- Quiz and recommendations ---

@app.route("/quiz", methods=["GET"])
def quiz():
    # render a questionnaire page (templates/quiz.html)
    return render_template("quiz.html")


# Accept both GET and POST so browser redirects to /recommend (GET) don't 404.
# POST: form submit from the quiz -> compute matches and render recommendations.
# GET: if user is authenticated, show recommendations for current user; else redirect to quiz.
@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    if request.method == "GET":
        # if logged-in user, you may show personalized recommendations (optional).
        if current_user.is_authenticated:
            # Construct a lightweight user-like object for matching from current_user fields
            user_like = current_user
            tracks = []  # fallback: you can call your match logic here if you have one that accepts current_user
            # Example: tracks = match_tracks(user_like, db.session)
            return render_template("recommendations.html", user=current_user, tracks=tracks)
        # otherwise send them to quiz to fill details
        return redirect(url_for("quiz"))

    # POST path: data came from quiz form
    name = request.form.get("name") or "Anonymous"
    age = request.form.get("age")
    #pincode = request.form.get("pincode")
    education = request.form.get("education")
    #language = request.form.get("language")
    interests = request.form.get("interests")  # can be comma-separated
    skill_level = request.form.get("skill_level")  # Beginner/Intermediate/Advanced

    # optionally persist the user info to DB for analytics (non-authenticated)
    new_user = User(
        name=name,
        age=(int(age) if age else None),
        #pincode=pincode,
        education=education,
        #language=language,
        interests=interests,
        skill_level=skill_level,
        # email/phone/password not set for anonymous quiz submit
    )
    db.session.add(new_user)
    db.session.commit()

    # call your matching function (ensure match_tracks imported from match.py)
    from match import match_tracks  # local import so file loads models first
    tracks = match_tracks(new_user, db.session)

    return render_template("recommendations.html", user=new_user, tracks=tracks)

DEV_ADMIN_KEY = os.environ.get("DEV_ADMIN_KEY", "dev-secret")

@app.route('/dev-set-password', methods=['POST'])
def dev_set_password():
    key = request.headers.get('X-DEV-KEY') or request.args.get('key')
    if key != DEV_ADMIN_KEY:
        return jsonify({'error': 'Not authorized'}), 403

    data = request.json or {}
    email = (data.get('email') or "").strip().lower()
    new_pwd = data.get('password')
    if not email or not new_pwd:
        return jsonify({'error':'email and password required'}), 400

    user = User.query.filter(func.lower(User.email) == email).first()
    if not user:
        return jsonify({'error':'user not found'}), 404

    if hasattr(user, 'set_password'):
        user.set_password(new_pwd)
    else:
        user.password_hash = generate_password_hash(new_pwd)
    db.session.commit()
    return jsonify({'message':'password set for '+email}), 200

# --- Run --------------------------------------------------------------------
if __name__ == '__main__':
    # ensure tables exist (in dev only). If you use migrations, remove this.
    with app.app_context():
        db.create_all()
    app.run(debug=True)

