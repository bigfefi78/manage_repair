import os
from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, Riparazione, STATI, STATI_BADGE, TIPI_DISPOSITIVO
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'gestione-riparazioni-dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///riparazioni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    totale = Riparazione.query.count()
    conteggi = {stato: Riparazione.query.filter_by(stato=stato).count() for stato in STATI}
    ultime = Riparazione.query.order_by(Riparazione.data_creazione.desc()).limit(5).all()
    return render_template('index.html', totale=totale, conteggi=conteggi, ultime=ultime,
                           stati=STATI, stati_badge=STATI_BADGE)


@app.route('/riparazioni')
def lista_riparazioni():
    filtro_stato = request.args.get('stato', '')
    query = Riparazione.query
    if filtro_stato and filtro_stato in STATI:
        query = query.filter_by(stato=filtro_stato)
    riparazioni = query.order_by(Riparazione.data_creazione.desc()).all()
    return render_template('riparazioni/lista.html', riparazioni=riparazioni,
                           stati=STATI, stati_badge=STATI_BADGE, filtro_stato=filtro_stato)


@app.route('/riparazioni/nuova', methods=['GET', 'POST'])
def nuova_riparazione():
    if request.method == 'POST':
        costo_raw = request.form.get('costo', '').strip()
        try:
            costo = float(costo_raw) if costo_raw else None
        except ValueError:
            costo = None
        riparazione = Riparazione(
            nome_cliente=request.form['nome_cliente'].strip(),
            telefono_cliente=request.form['telefono_cliente'].strip(),
            tipo_dispositivo=request.form['tipo_dispositivo'],
            marca_modello=request.form['marca_modello'].strip(),
            descrizione_problema=request.form['descrizione_problema'].strip(),
            stato=request.form.get('stato', 'in_attesa'),
            tecnico=request.form.get('tecnico', '').strip() or None,
            costo=costo,
            note=request.form.get('note', '').strip() or None,
        )
        db.session.add(riparazione)
        db.session.commit()
        flash('Riparazione creata con successo!', 'success')
        return redirect(url_for('dettaglio_riparazione', id=riparazione.id))
    return render_template('riparazioni/nuova.html', stati=STATI, tipi=TIPI_DISPOSITIVO)


@app.route('/riparazioni/<int:id>')
def dettaglio_riparazione(id):
    riparazione = db.get_or_404(Riparazione, id)
    return render_template('riparazioni/dettaglio.html', riparazione=riparazione,
                           stati=STATI, stati_badge=STATI_BADGE)


@app.route('/riparazioni/<int:id>/modifica', methods=['GET', 'POST'])
def modifica_riparazione(id):
    riparazione = db.get_or_404(Riparazione, id)
    if request.method == 'POST':
        riparazione.nome_cliente = request.form['nome_cliente'].strip()
        riparazione.telefono_cliente = request.form['telefono_cliente'].strip()
        riparazione.tipo_dispositivo = request.form['tipo_dispositivo']
        riparazione.marca_modello = request.form['marca_modello'].strip()
        riparazione.descrizione_problema = request.form['descrizione_problema'].strip()
        riparazione.stato = request.form.get('stato', riparazione.stato)
        riparazione.tecnico = request.form.get('tecnico', '').strip() or None
        costo_raw = request.form.get('costo', '').strip()
        try:
            riparazione.costo = float(costo_raw) if costo_raw else None
        except ValueError:
            riparazione.costo = None
        riparazione.note = request.form.get('note', '').strip() or None
        riparazione.data_aggiornamento = datetime.now(timezone.utc)
        db.session.commit()
        flash('Riparazione aggiornata con successo!', 'success')
        return redirect(url_for('dettaglio_riparazione', id=riparazione.id))
    return render_template('riparazioni/modifica.html', riparazione=riparazione,
                           stati=STATI, tipi=TIPI_DISPOSITIVO)


@app.route('/riparazioni/<int:id>/elimina', methods=['POST'])
def elimina_riparazione(id):
    riparazione = db.get_or_404(Riparazione, id)
    db.session.delete(riparazione)
    db.session.commit()
    flash('Riparazione eliminata.', 'info')
    return redirect(url_for('lista_riparazioni'))


if __name__ == '__main__':
    app.run(debug=False)
