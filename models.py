from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

STATI = {
    'in_attesa': 'In Attesa',
    'in_lavorazione': 'In Lavorazione',
    'completata': 'Completata',
    'consegnata': 'Consegnata',
}

STATI_BADGE = {
    'in_attesa': 'warning',
    'in_lavorazione': 'primary',
    'completata': 'success',
    'consegnata': 'secondary',
}

TIPI_DISPOSITIVO = ['Smartphone', 'Laptop', 'Tablet', 'Computer', 'Stampante', 'Altro']


class Riparazione(db.Model):
    __tablename__ = 'riparazioni'

    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    telefono_cliente = db.Column(db.String(30), nullable=False)
    tipo_dispositivo = db.Column(db.String(50), nullable=False)
    marca_modello = db.Column(db.String(100), nullable=False)
    descrizione_problema = db.Column(db.Text, nullable=False)
    stato = db.Column(db.String(20), nullable=False, default='in_attesa')
    tecnico = db.Column(db.String(100), nullable=True)
    costo = db.Column(db.Numeric(10, 2), nullable=True)
    note = db.Column(db.Text, nullable=True)
    data_creazione = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    data_aggiornamento = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def stato_label(self):
        return STATI.get(self.stato, self.stato)

    def stato_badge(self):
        return STATI_BADGE.get(self.stato, 'secondary')
