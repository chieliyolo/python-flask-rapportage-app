from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database model voor gebruikers
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class LoginForm(FlaskForm):
    username = StringField('Gebruikersnaam', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Wachtwoord', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Gebruikersnaam', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Wachtwoord', validators=[DataRequired()])
    confirm_password = PasswordField('Bevestig Wachtwoord', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registreer')

# Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Gebruikersnaam bestaat al.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registratie succesvol. Log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Succesvol ingelogd.', 'success')
            return redirect(url_for('upload_file'))
        flash('Ongeldige inloggegevens.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Je bent uitgelogd.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
@login_required
def process_file():
    file = request.files['file']
    df = pd.read_excel(file)

    artikel_data = df[(df['Artnr.'] == '000001') & (df['Benaming project'].str.contains('OCMW'))]
    artikel_data = artikel_data[artikel_data['Benaming project'] != 'Geen OCMW bijdrage']
    artikel_data['Aantal'] = pd.to_numeric(artikel_data['Aantal'], errors='coerce') 
    project_som = artikel_data.groupby('Benaming project')['Aantal'].sum()
    totaal_aantal = round(project_som.sum(), 2)

    plt.figure(figsize=(8, 6))
    plt.pie(project_som, labels=project_som.index, autopct=lambda p: f'{p * totaal_aantal / 100:.2f}', startangle=90)
    plt.title(f'Spreiding werkuren per OCMW (Totaal: {totaal_aantal})')
    plt.axis('equal')
    plt.tight_layout()

    graph_path = os.path.join('static', 'graph.png')
    plt.savefig(graph_path, format='png', bbox_inches='tight')
    plt.close()

    tabel_data = project_som.reset_index().rename(columns={'Benaming project': 'Project', 'Aantal': 'Werkuren'})
    tabel_data['Werkuren'] = tabel_data['Werkuren'].round(2)
    tabel_data = tabel_data.to_dict(orient='records')
    totaal_werkuren = round(project_som.sum(), 2)

    return render_template('index.html', graph_url='/static/graph.png', tabel_data=tabel_data, totaal_werkuren=totaal_werkuren)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
