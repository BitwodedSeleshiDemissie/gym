# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime

app = Flask(__name__)
app.config.update(
    SECRET_KEY='secret-key',
    SQLALCHEMY_DATABASE_URI='sqlite:///app.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(150))
    text = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='yonas').first():
        u1 = User(username='yonas', password='yonas')
        u2 = User(username='bitwoded', password='bitwoded')
        db.session.add_all([u1, u2])
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        user = User.query.filter_by(username=u, password=p).first()
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
    out = []
    for b in Booking.query.all():
        out.append({
            'id': b.id,
            'start': b.start.isoformat(),
            'end': b.end.isoformat(),
            'color': 'red' if b.user_id == current_user.id else 'blue',
            'user_id': b.user_id
        })
    return jsonify(out)

@app.route('/book', methods=['POST'])
@login_required
def book():
    data = request.get_json()
    start = datetime.fromisoformat(data['start'])
    end   = datetime.fromisoformat(data['end'])
    if Booking.query.filter(Booking.start < end, Booking.end > start).first():
        return jsonify({'status': 'conflict'}), 400
    b = Booking(user_id=current_user.id, start=start, end=end)
    db.session.add(b)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/booking/<int:booking_id>', methods=['DELETE'])
@login_required
def delete_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)
    if b.user_id != current_user.id:
        abort(403)
    db.session.delete(b)
    db.session.commit()
    return jsonify({'status': 'deleted'})

@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    if request.method == 'POST':
        txt = request.get_json().get('text')
        m = Message(user_id=current_user.id, username=current_user.username, text=txt)
        db.session.add(m)
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
