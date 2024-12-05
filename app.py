from flask import Flask, request, render_template
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import time

app = Flask(__name__)

# Maak een map om de grafieken op te slaan
if not os.path.exists('static'):
    os.makedirs('static')

def clean_static_folder():
    """Verwijder oude grafieken om opslagruimte vrij te maken."""
    for file in glob.glob('static/*.png'):
        if time.time() - os.path.getmtime(file) > 3600:  # Verwijder bestanden ouder dan 1 uur
            os.remove(file)

@app.route('/')
def upload_file():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    # Verwijder oude grafieken
    clean_static_folder()

    # Controleer of er een bestand is geüpload
    file = request.files['file']
    if not file:
        return "Geen bestand geüpload, probeer opnieuw.", 400

    try:
        # Lees de Excel-data
        df = pd.read_excel(file)

        # Filter de data voor artikel 000001
        artikel_data = df[(df['Artnr.'] == '000001') & (df['Benaming project'].notna())]
        artikel_data = artikel_data[artikel_data['Benaming project'].str.contains('OCMW')]
        artikel_data = artikel_data[artikel_data['Benaming project'] != 'Geen OCMW bijdrage']

        artikel_data['Aantal'] = pd.to_numeric(artikel_data['Aantal'], errors='coerce') 
        project_som = artikel_data.groupby('Benaming project')['Aantal'].sum()
        totaal_aantal = round(project_som.sum(), 2)

        # Maak het taartdiagram
        def format_autopct(pct):
            absolute = pct * totaal_aantal / 100
            return f'{absolute:.2f} ({pct:.1f}%)'

        plt.figure(figsize=(8, 6))
        plt.pie(project_som, labels=project_som.index, autopct=format_autopct, startangle=90)
        plt.title(f'Spreiding werkuren per OCMW (Totaal: {totaal_aantal})')
        plt.axis('equal')
        plt.tight_layout()

        # Sla de grafiek op in de static-map
        graph_path = os.path.join('static', 'graph.png')
        plt.savefig(graph_path, format='png', bbox_inches='tight')
        plt.close()

        # Converteer de gegevens naar een lijst met dicts en rond af
        tabel_data = project_som.reset_index().rename(columns={'Benaming project': 'Project', 'Aantal': 'Werkuren'})
        tabel_data['Werkuren'] = tabel_data['Werkuren'].round(2)
        tabel_data = tabel_data.to_dict(orient='records')

        # Totale werkuren berekenen
        totaal_werkuren = round(project_som.sum(), 2)

        # Geef de grafiek en tabel terug aan de pagina
        return render_template('index.html', graph_url='/static/graph.png', tabel_data=tabel_data, totaal_werkuren=totaal_werkuren)

    except Exception as e:
        return f"Er ging iets mis bij het verwerken van het bestand: {e}", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
