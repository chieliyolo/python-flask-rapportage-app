from flask import Flask, request, render_template, send_file
import pandas as pd
import matplotlib.pyplot as plt
import os
from io import BytesIO

app = Flask(__name__)

# Maak een map om de grafieken op te slaan
if not os.path.exists('static'):
    os.makedirs('static')

@app.route('/')
def upload_file():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    file = request.files['file']
    df = pd.read_excel(file)

    # Filter de data voor artikel 000001
    artikel_data = df[(df['Artnr.'] == '000001') & (df['Benaming project'].str.contains('OCMW'))]
    artikel_data = artikel_data[artikel_data['Benaming project'] != 'Geen OCMW bijdrage']

    artikel_data['Aantal'] = pd.to_numeric(artikel_data['Aantal'], errors='coerce') 
    project_som = artikel_data.groupby('Benaming project')['Aantal'].sum()
    totaal_aantal = round(project_som.sum(), 2)

    # Maak het taartdiagram
    plt.figure(figsize=(10, 10))
    plt.pie(project_som, labels=project_som.index, autopct=lambda p: f'{p * totaal_aantal / 100:.2f}', startangle=90)
    plt.title(f'Spreiding werkuren per OCMW (Totaal: {totaal_aantal})')
    plt.axis('equal')
    plt.tight_layout()

    # Sla de figuur op in geheugen
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)

    # Converteer de gegevens naar een lijst met dicts (geschikt voor HTML-rendering)
    tabel_data = project_som.reset_index().rename(columns={'Benaming project': 'Project', 'Aantal': 'Werkuren'}).to_dict(orient='records')

    # Geef de grafiek en tabel terug aan de pagina
    return render_template('index.html', graph_url='/static/graph.png', tabel_data=tabel_data)

@app.route('/static/graph.png')
def graph():
    return send_file('static/graph.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
