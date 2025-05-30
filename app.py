# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Use Render PostgreSQL connection directly
DATABASE_URL = 'postgresql://gym_8qkl_user:gwt1spB0iyEDQVPu4NU1ZYOOhR8R5qRd@dpg-d0sr87c9c44c73ff2n1g-a/gym_8qkl'
SECRET_KEY = 'your-secret-key-here'  # replace with your Flask secret

app.config.update(
    SECRET_KEY=SECRET_KEY,
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables and seed default users
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='yonas').first():
        seed_users = [
            User(username='yonas', password='yonas'),
            User(username='bitwoded', password='bitwoded')
        ]
        db.session.add_all(seed_users)
        db.session.commit()

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/events')
@login_required
def events():
    events = []
    for b in Booking.query.all():
        events.append({
            'id': b.id,
            'start': b.start.isoformat(),
            'end': b.end.isoformat(),
            'color': 'red' if b.user_id == current_user.id else 'blue',
            'user_id': b.user_id
        })
    return jsonify(events)

@app.route('/book', methods=['POST'])
@login_required
def book():
    data = request.get_json()
    start = datetime.fromisoformat(data['start'])
    end = datetime.fromisoformat(data['end'])
    conflict = Booking.query.filter(Booking.start < end, Booking.end > start).first()
    if conflict:
        return jsonify({'status': 'conflict'}), 400
    new_booking = Booking(user_id=current_user.id, start=start, end=end)
    db.session.add(new_booking)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/booking/<int:booking_id>', methods=['DELETE'])
@login_required
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        abort(403)
    db.session.delete(booking)
    db.session.commit()
    return jsonify({'status': 'deleted'})

@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    if request.method == 'POST':
        text = request.get_json().get('text')
        msg = Message(user_id=current_user.id, username=current_user.username, text=text)
        db.session.add(msg)
        db.session.commit()
        return jsonify({'status': 'ok'})
    msgs = Message.query.order_by(Message.timestamp.asc()).all()
    return jsonify([{
        'username': m.username,
        'text': m.text,
        'time': m.timestamp.strftime('%H:%M')
    } for m in msgs])

if __name__ == '__main__':
    app.run(debug=True)