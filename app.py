from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime, time
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__, template_folder="templates", static_folder="static")

def get_db_connection():
    conn = sqlite3.connect("turnos.db")
    conn.row_factory = sqlite3.Row
    return conn

def enviar_email(destinatario, asunto, cuerpo):
    remitente = "paulagarrocho@gmail.com"  # Cambiar por tu correo
    contraseña = "xmrt jppy eiml rapf"  # Contraseña de aplicación (no tu clave normal)

    mensaje = EmailMessage()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(remitente, contraseña)
        smtp.send_message(mensaje)

# Crear tabla si no existe
with get_db_connection() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS turnos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL)''')
    conn.commit()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/reservar", methods=["POST"])
def reservar_turno():
    data = request.json

    # Validar que estén todos los campos
    if not all(k in data for k in ("cliente", "fecha", "hora")):
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    # Validar formato de fecha y hora
    try:
        turno_datetime = datetime.strptime(f"{data['fecha']} {data['hora']}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Formato de fecha u hora inválido"}), 400

    # Validar que no sea en el pasado
    if turno_datetime < datetime.now():
        return jsonify({"error": "No se puede reservar un turno en el pasado"}), 400

    # Validar que no sea domingo (domingo = 6)
    if turno_datetime.weekday() == 6:
        return jsonify({"error": "La peluquería no abre los domingos"}), 400

    # Validar rango horario permitido (10:00 a 20:00)
    hora_turno = turno_datetime.time()
    if not (time(10, 0) <= hora_turno <= time(20, 0)):
        return jsonify({"error": "El horario debe estar entre las 10:00 y las 20:00"}), 400

    # Validar si ya existe un turno reservado en esa fecha y hora
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM turnos WHERE fecha = ? AND hora = ?",
                            (data['fecha'], data['hora'])).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Ya hay un turno reservado en esa fecha y hora"}), 409

    # Guardar el turno
    conn.execute("INSERT INTO turnos (cliente, fecha, hora) VALUES (?, ?, ?)",
                 (data['cliente'], data['fecha'], data['hora']))
    conn.commit()
    conn.close()

    # Enviar notificación por email
    try:
        enviar_email(
            destinatario="Lusail.barberia@gmail.com",
            asunto="Nuevo turno reservado",
            cuerpo=f"Nuevo turno reservado por {data['cliente']} el {data['fecha']} a las {data['hora']}"
        )
    except Exception as e:
        print(f"Error al enviar email: {e}")

    return jsonify({"mensaje": "Turno reservado exitosamente"}), 201

@app.route("/turnos", methods=["GET"])
def listar_turnos():
    conn = get_db_connection()
    turnos = conn.execute("SELECT * FROM turnos").fetchall()
    conn.close()
    return jsonify([dict(turno) for turno in turnos])

@app.route("/cancelar", methods=["POST"])
def cancelar_turno():
    data = request.json

    if not all(k in data for k in ("cliente", "fecha", "hora")):
        return jsonify({"error": "Faltan datos para cancelar el turno"}), 400

    conn = get_db_connection()
    conn.execute("DELETE FROM turnos WHERE cliente = ? AND fecha = ? AND hora = ?",
                 (data["cliente"], data["fecha"], data["hora"]))
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Turno cancelado correctamente"}), 200

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)
    
