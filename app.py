from flask import Flask, request, render_template, send_file
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def upload_file():
    return '''
    <h1>Upload je Excel-bestand</h1>
    <form action="/process" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Genereer Grafiek">
    </form>
    '''

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

    return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)