import smtplib
from email.mime.text import MIMEText

import bcrypt
import uuid
from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from datetime import datetime


def setup_auth_routes(app, users_collection):
    @app.route('/')
    def index():
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            name = request.form['name']
            surname = request.form['surname']
            Gender = request.form['Gender']
            birthdate = request.form['birthdate']
            email = request.form['email']

            # Check if user already exists
            existing_user = users_collection.find_one({"username": username})
            if existing_user:
                flash('Username already exists. Please choose another.', 'error')
                return redirect(url_for('register'))

            existing_email = users_collection.find_one({"email": email})
            if existing_email:
                flash('Este correo ya está registrado.', 'error')
                return redirect(url_for('register'))

            # Generate a unique user ID
            last_user = users_collection.find_one(sort=[("user_id", -1)])
            user_id = (last_user["user_id"] + 1) if last_user else 1000

            # Hash the password
            hashed_password = generate_password_hash(password)

            # Create user document
            user_data = {
                "user_id": user_id,
                "username": username,
                "password": hashed_password,
                "name": name,
                "surname": surname,
                "Gender": Gender,
                "birthdate": birthdate,
                "email": email,
                "report_count": 0,
                "created_at": datetime.now()
            }

            # Insert user into database
            users_collection.insert_one(user_data)

            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            # Find user
            user = users_collection.find_one({"username": username})

            if user and bcrypt.checkpw(password.encode(), user['password']):
                # Create session
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['name'] = user['name']
                session['surname'] = user['surname']
                session['birthdate'] = user['birthdate']
                session['Gender'] = user['Gender']

                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')

        return render_template('login.html')

    @app.route('/forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            username = request.form['username']
            user = users_collection.find_one({"username": username})

            if user:
                token = str(uuid.uuid4())
                users_collection.update_one(
                    {"user_id": user['user_id']},
                    {"$set": {"reset_token": token}}
                )
                enlace = url_for('reset_password', token=token, _external=True)
                enviar_correo(user['email'], enlace)
                flash("📩 Correo enviado con éxito. ¡Revisa tu bandeja de entrada y la carpeta de spam!", "success")
                return redirect(url_for('login'))
            else:
                flash('Usuario no encontrado.', 'danger')
        return render_template('forgot_password.html')

    @app.route('/reset_password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        user = users_collection.find_one({"reset_token": token})

        if not user:
            return "Token inválido o expirado."

        if request.method == 'POST':
            nueva_password = request.form['password']

            # Generar un salt y el hash de la nueva contraseña
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(nueva_password.encode(), salt)

            # Actualizar la contraseña en la base de datos
            users_collection.update_one(
                {"user_id": user['user_id']},
                {"$set": {"password": hashed_password}, "$unset": {"reset_token": ""}}
            )
            flash('Contraseña actualizada correctamente.', 'success')
            return redirect(url_for('login'))

        return render_template('reset_password.html')


def enviar_correo(destinatario, enlace):
    """
    Envía un correo electrónico para restablecer la contraseña

    Args:
        destinatario (str): Dirección de correo del usuario
        enlace (str): Enlace para restablecer la contraseña
    """
    remitente = "terabytetitans@gmail.com"
    app_password = "wnhm ozuw uuym prnm"

    cuerpo = f"""
    ¡Hola! 👋

    Recibimos una solicitud para restablecer tu contraseña. Haz clic en el siguiente enlace para continuar:

    🔗 {enlace}

    Este enlace expirará en 1 hora. Si no solicitaste este cambio, ignora este mensaje.

    - El equipo de PREOBES 💻
    """

    msg = MIMEText(cuerpo, _charset="utf-8")
    msg['Subject'] = '🔒 Recupera tu contraseña'
    msg['From'] = remitente
    msg['To'] = destinatario

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(remitente, app_password)
        server.sendmail(remitente, destinatario, msg.as_string())