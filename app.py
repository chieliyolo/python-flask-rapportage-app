from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import matplotlib.pyplot as plt
import os

# Controleer of de 'static' map bestaat, anders maak je deze aan
if not os.path.exists('static'):
    os.makedirs('static')
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Vervang door een sterke sleutel
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite-database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database model voor gebruikers
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Loginformulier
class LoginForm(FlaskForm):
    username = StringField('Gebruikersnaam', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Wachtwoord', validators=[DataRequired()])
    submit = SubmitField('Login')

# Registratieformulier
class RegisterForm(FlaskForm):
    username = StringField('Gebruikersnaam', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Wachtwoord', validators=[DataRequired()])
    confirm_password = PasswordField('Bevestig Wachtwoord', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registreer')

# Maak de database aan
with app.app_context():
    db.create_all()

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
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Succesvol ingelogd.', 'success')
            return redirect(url_for('upload_file'))
        flash('Ongeldige inloggegevens.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('Je bent uitgelogd.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/index')
def upload_file():
    print("Route /index of / aangeroepen")
    if 'user_id' not in session:
        flash('Log in om verder te gaan.', 'warning')
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    if 'user_id' not in session:
        flash('Log in om deze actie uit te voeren.', 'warning')
        return redirect(url_for('login'))

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
