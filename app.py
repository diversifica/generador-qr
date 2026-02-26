from flask import Flask, request, render_template_string, redirect, url_for, flash
import qrcode
from PIL import Image
import io
import base64
import os
import json
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, login_user, logout_user, login_required, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secreto-cambiar-en-produccion'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qrs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    qrs = db.relationship('DynamicQR', backref='user', lazy=True)
    designs = db.relationship('Design', backref='user', lazy=True)

class DynamicQR(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data = db.Column(db.Text, nullable=False)
    fill_color = db.Column(db.String(20), default='#000000')
    back_color = db.Column(db.String(20), default='#ffffff')
    logo_base64 = db.Column(db.Text, nullable=True)

class Design(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fill_color = db.Column(db.String(20), default='#000000')
    back_color = db.Column(db.String(20), default='#ffffff')
    logo_base64 = db.Column(db.Text, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Plantillas HTML ---
HMTL_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador de Código QR con Logo</title>
    <!-- CSS de Cropper.js -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-color: #f0f2f5;
            --container-bg: white;
            --text-color: #333;
            --label-color: #555;
            --input-bg: white;
            --input-border: #ccc;
            --button-primary-bg: #007bff;
            --button-primary-hover-bg: #0056b3;
            --button-secondary-bg: #6c757d;
            --button-secondary-hover-bg: #5a6268;
            --button-success-bg: #28a745;
            --button-success-hover-bg: #218838;
            --box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .dark-mode {
            --bg-color: #1a1a1a;
            --container-bg: #242424;
            --text-color: #f8f8f8;
            --label-color: #cccccc;
            --input-bg: #333333;
            --input-border: #555555;
            --button-primary-bg: #2979ff;
            --button-primary-hover-bg: #1565c0;
            --button-secondary-bg: #555;
            --button-secondary-hover-bg: #444;
            --button-success-bg: #2e7d32;
            --button-success-hover-bg: #1b5e20;
            --box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }

        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background-color: var(--bg-color); transition: background-color 0.3s ease; }
        .container { background: var(--container-bg); padding: 40px; border-radius: 12px; box-shadow: var(--box-shadow); width: 90%; max-width: 500px; transition: background-color 0.3s ease, box-shadow 0.3s ease; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h1 { color: var(--text-color); margin: 0; font-size: 1.4rem; transition: color 0.3s ease; }
        label { font-weight: 500; color: var(--label-color); display: block; margin: 15px 0 5px; transition: color 0.3s ease; }
        input[type="text"], input[type="file"] { width: calc(100% - 24px); padding: 12px; margin-bottom: 10px; border: 1px solid var(--input-border); border-radius: 6px; font-size: 16px; background-color: var(--input-bg); color: var(--text-color); transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease; }
        .color-selectors { display: flex; justify-content: center; gap: 20px; margin: 10px 0; }
        input[type="color"] { width: 50px; height: 50px; border: none; border-radius: 8px; cursor: pointer; }
        .button-group { margin-top: 10px; display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; }
        .btn { color: white; padding: 12px 25px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; text-decoration: none; display: inline-block; transition: background-color 0.3s ease; }
        .btn-primary { background-color: var(--button-primary-bg); }
        .btn-primary:hover { background-color: var(--button-primary-hover-bg); }
        .btn-success { background-color: var(--button-success-bg); }
        .btn-success:hover { background-color: var(--button-success-hover-bg); }
        .btn-secondary { background-color: var(--button-secondary-bg); }
        .btn-secondary:hover { background-color: var(--button-secondary-hover-bg); }

        .qr-container {
            margin-top: 25px;
            min-height: 250px; /* Altura mínima para evitar el salto */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        img { max-width: 100%; height: auto; }
        
        /* Estilos para el Modal de recorte */
        #crop-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center; }
        #crop-container { background: var(--container-bg); padding: 20px; border-radius: 8px; max-width: 90vw; max-height: 80vh; transition: background-color 0.3s ease; }
        #image-to-crop { max-height: 60vh; }

        /* Estilos para el deslizador de modo oscuro */
        .theme-switch-wrapper {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            width: auto;
        }
        .theme-switch {
            display: inline-block;
            height: 34px;
            position: relative;
            width: 60px;
        }
        .theme-switch input { display:none; }
        .slider {
            background-color: #ccc;
            bottom: 0;
            cursor: pointer;
            left: 0;
            position: absolute;
            right: 0;
            top: 0;
            transition: .4s;
            border-radius: 34px;
        }
        .slider:before {
            background-color: #fff;
            bottom: 4px;
            content: "";
            height: 26px;
            left: 4px;
            position: absolute;
            transition: .4s;
            width: 26px;
            border-radius: 50%;
        }
        input:checked + .slider { background-color: #2196F3; }
        input:checked + .slider:before { transform: translateX(26px); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Generador de Código QR con Logo v.1</h1>
            <div class="theme-switch-wrapper">
                <label class="theme-switch" for="checkbox">
                    <input type="checkbox" id="checkbox" />
                    <div class="slider round"></div>
                </label>
                <span style="margin-left: 10px; color: var(--label-color);">Modo Oscuro</span>
            </div>
        </div>
        {% if current_user.is_authenticated %}
        <div style="width: 100%; text-align: right; margin-bottom: 20px; font-size: 0.9em; color: var(--text-color);">
            Usuario: <strong>{{ current_user.email }}</strong> | <a href="{{ url_for('logout') }}" style="color: var(--button-primary-bg); text-decoration: none;">Cerrar sesión</a>
        </div>
        {% endif %}
        <form action="/" method="post" enctype="multipart/form-data" id="qr-form">
            <label for="data">Introduce el texto o URL:</label>
            <input type="text" id="data" name="data" value="{{ data or '' }}" required>
            <div class="color-selectors">
                <div><label for="fill_color">Color QR:</label><input type="color" id="fill_color" name="fill_color" value="{{ fill_color or '#000000' }}"></div>
                <div><label for="back_color">Fondo:</label><input type="color" id="back_color" name="back_color" value="{{ back_color or '#ffffff' }}"></div>
            </div>
            <label for="design-select">Usar diseño guardado:</label>
            <select id="design-select" style="width: 100%; padding: 10px; margin-bottom: 10px;">
                <option value="">-- Seleccionar --</option>
                {% for name in designs %}
                <option value="{{ name }}">{{ name }}</option>
                {% endfor %}
            </select>

            <label for="design-name">Guardar diseño como:</label>
            <input type="text" id="design-name" placeholder="Nombre del diseño">
            <button type="button" id="save-design-button" class="btn btn-secondary" style="width:100%">Guardar Diseño</button>

            <label for="logo-input">Logo (opcional, se recortará a formato cuadrado):</label>
            <input type="file" id="logo-input" accept="image/*">
            <!-- Campo oculto para guardar la imagen recortada en Base64 -->
            <input type="hidden" id="logo_base64" name="logo_base64" value="{{ logo_base64 or '' }}">
            <label style="margin-top:10px;">
                <input type="checkbox" id="dynamic" name="dynamic" {% if dynamic %}checked{% endif %}>
                QR dinámico (redirección editable)
            </label>
            <div class="button-group">
                <button type="submit" id="generate-qr-button" class="btn btn-primary">Generar QR</button>
                <button type="button" id="generate-export-button" class="btn btn-success">Generar QR y Exportar</button>
                <button type="button" id="new-qr-button" class="btn btn-success">Nuevo QR</button>
            </div>
        </form>
        <div class="qr-container" style="{% if not qr_image %}display: none;{% endif %}">
            {% if qr_image %}
                <h2>Tu Código QR:</h2>
                <img src="data:image/png;base64,{{ qr_image }}" alt="Código QR Generado">
                <a href="data:image/png;base64,{{ qr_image }}" class="btn btn-success download-btn" download="codigo_qr.png" id="actual-download-button" style="margin-top:15px;">Descargar QR</a>
                {% if dynamic_id %}
                    <a href="{{ url_for('edit_dynamic', qr_id=dynamic_id) }}" class="btn btn-secondary edit-link" style="margin-top:10px;">Editar redirección</a>
                {% endif %}
            {% endif %}
        </div>
    </div>

    <!-- Modal para recortar la imagen -->
    <div id="crop-modal">
        <div id="crop-container">
            <h2>Recortar Logo</h2>
            <div><img id="image-to-crop"></div>
            <button type="button" id="crop-button" class="btn btn-primary" style="margin-top:15px;">Confirmar Recorte</button>
        </div>
    </div>

    <!-- JS de Cropper.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
    <!-- JS Personalizado -->
    <script>
        const logoInput = document.getElementById('logo-input');
        const modal = document.getElementById('crop-modal');
        const imageToCrop = document.getElementById('image-to-crop');
        const cropButton = document.getElementById('crop-button');
        const hiddenInput = document.getElementById('logo_base64');
        const newQrButton = document.getElementById('new-qr-button');
        const generateQrButton = document.getElementById('generate-qr-button');
        const generateExportButton = document.getElementById('generate-export-button');
        const actualDownloadButton = document.getElementById('actual-download-button');
        const qrContainer = document.querySelector('.qr-container');
        const themeToggle = document.getElementById('checkbox');
        const body = document.body;
        const qrForm = document.getElementById('qr-form');
        const designSelect = document.getElementById('design-select');
        const designNameInput = document.getElementById('design-name');
        const saveDesignButton = document.getElementById('save-design-button');
        const designs = {{ designs_json | safe }};

        let cropper;
        let shouldExport = false; // Bandera para controlar la exportación

        // --- Lógica del Modo Oscuro ---
        const currentTheme = localStorage.getItem('theme');
        if (currentTheme === 'dark' || !currentTheme) { // Modo oscuro por defecto
            body.classList.add('dark-mode');
            themeToggle.checked = true;
        } else {
            themeToggle.checked = false;
        }

        themeToggle.addEventListener('change', () => {
            if (themeToggle.checked) {
                body.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark');
            } else {
                body.classList.remove('dark-mode');
                localStorage.setItem('theme', 'light');
            }
        });

        // --- Lógica de Cropper.js ---
        logoInput.addEventListener('change', (e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    imageToCrop.src = event.target.result;
                    modal.style.display = 'flex';
                    if (cropper) {
                        cropper.destroy();
                    }
                    cropper = new Cropper(imageToCrop, {
                        aspectRatio: 1 / 1, // Proporción cuadrada
                        viewMode: 1,
                        dragMode: 'move',
                        background: false,
                        autoCropArea: 0.8
                    });
                };
                reader.readAsDataURL(files[0]);
            }
        });

        cropButton.addEventListener('click', () => {
            const canvas = cropper.getCroppedCanvas({
                width: 256, // Tamaño fijo para el logo
                height: 256,
                imageSmoothingQuality: 'high',
            });
            hiddenInput.value = canvas.toDataURL('image/png');
            modal.style.display = 'none';
            cropper.destroy();
            // Opcional: mostrar un feedback de que el logo se cargó
            logoInput.style.border = '2px solid var(--button-success-bg)';
        });

        // --- Cargar diseño seleccionado ---
        if (designSelect) {
            designSelect.addEventListener('change', () => {
                const name = designSelect.value;
                if (designs[name]) {
                    document.getElementById('fill_color').value = designs[name].fill_color || '#000000';
                    document.getElementById('back_color').value = designs[name].back_color || '#ffffff';
                    hiddenInput.value = designs[name].logo_base64 || '';
                }
            });
        }

        // --- Guardar diseño actual ---
        if (saveDesignButton) {
            saveDesignButton.addEventListener('click', async () => {
                const name = designNameInput.value.trim();
                if (!name) {
                    alert('Debes proporcionar un nombre para el diseño');
                    return;
                }
                const formData = new FormData();
                formData.append('name', name);
                formData.append('fill_color', document.getElementById('fill_color').value);
                formData.append('back_color', document.getElementById('back_color').value);
                formData.append('logo_base64', hiddenInput.value);
                const resp = await fetch('/save_design', { method: 'POST', body: formData });
                if (resp.ok) {
                    designs[name] = {
                        fill_color: formData.get('fill_color'),
                        back_color: formData.get('back_color'),
                        logo_base64: formData.get('logo_base64')
                    };
                    const option = document.createElement('option');
                    option.value = name;
                    option.textContent = name;
                    designSelect.appendChild(option);
                    designNameInput.value = '';
                    alert('Diseño guardado');
                } else {
                    alert('Error al guardar el diseño');
                }
            });
        }

        // --- Lógica del botón Nuevo QR ---
        newQrButton.addEventListener('click', () => {
            document.getElementById('data').value = '';
            document.getElementById('fill_color').value = '#000000';
            document.getElementById('back_color').value = '#ffffff';
            document.getElementById('logo_base64').value = '';
            logoInput.value = ''; // Limpiar el input de tipo file
            logoInput.style.border = ''; // Quitar el feedback visual
            qrContainer.style.display = 'none'; // Ocultar el contenedor del QR
        });

        // --- Lógica del botón Generar QR y Exportar ---
        generateExportButton.addEventListener('click', () => {
            shouldExport = true;
            generateQrButton.click(); // Simular clic en el botón de generar
        });

        // Interceptar el envío del formulario para manejar la exportación
        qrForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // Prevenir el envío normal del formulario

            const formData = new FormData(qrForm);
            const response = await fetch(qrForm.action, {
                method: qrForm.method,
                body: formData
            });
            const html = await response.text();

            // Crear un elemento temporal para parsear el HTML y extraer el QR
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newQrImageSrc = tempDiv.querySelector('.qr-container img')?.src;
            const newDownloadLink = tempDiv.querySelector('.qr-container a.download-btn')?.href;
            const newEditLink = tempDiv.querySelector('.qr-container a.edit-link')?.href;

            if (newQrImageSrc) {
                // Actualizar la imagen y el botón de descarga en la página actual
                qrContainer.innerHTML = `
                    <h2>Tu Código QR:</h2>
                    <img src="${newQrImageSrc}" alt="Código QR Generado">
                    <a href="${newDownloadLink}" class="btn btn-success download-btn" download="codigo_qr.png" id="actual-download-button" style="margin-top:15px;">Descargar QR</a>
                    ${newEditLink ? `<a href="${newEditLink}" class="btn btn-secondary edit-link" style="margin-top:10px;">Editar redirección</a>` : ''}
                `;
                qrContainer.style.display = 'flex';

                if (shouldExport) {
                    // Simular clic en el botón de descarga si shouldExport es true
                    const downloadLinkElement = qrContainer.querySelector('#actual-download-button');
                    if (downloadLinkElement) {
                        downloadLinkElement.click();
                    }
                    shouldExport = false; // Resetear la bandera
                }
            } else {
                // Manejar errores o mensajes del servidor
                qrContainer.style.display = 'none';
                alert("Error al generar el QR. Por favor, introduce datos válidos.");
            }
        });
    </script>
</body>
</html>
"""

AUTH_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        :root {
            --bg-color: #f0f2f5; --container-bg: white; --text-color: #333; --label-color: #555;
            --input-bg: white; --input-border: #ccc; --button-primary-bg: #007bff; --button-primary-hover-bg: #0056b3;
            --box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .dark-mode {
            --bg-color: #1a1a1a; --container-bg: #242424; --text-color: #f8f8f8; --label-color: #cccccc;
            --input-bg: #333333; --input-border: #555555; --button-primary-bg: #2979ff; --button-primary-hover-bg: #1565c0;
            --box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background-color: var(--bg-color); transition: background-color 0.3s ease; }
        .container { background: var(--container-bg); padding: 40px; border-radius: 12px; box-shadow: var(--box-shadow); width: 90%; max-width: 400px; text-align: center; }
        h2 { color: var(--text-color); margin-top: 0; margin-bottom: 25px;}
        label { display: block; text-align: left; margin: 15px 0 5px; color: var(--label-color); font-weight: 500;}
        input[type="email"], input[type="password"], input[type="text"] { width: calc(100% - 24px); padding: 12px; border: 1px solid var(--input-border); border-radius: 6px; background: var(--input-bg); color: var(--text-color); margin-bottom: 20px; font-size:16px;}
        .btn { color: white; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; width: 100%; display: block; box-sizing: border-box; font-size: 16px; background-color: var(--button-primary-bg); transition: background-color 0.3s ease; }
        .btn:hover { background-color: var(--button-primary-hover-bg); }
        .flash { color: #fff; margin-bottom: 15px; background: #e74c3c; padding: 10px; border-radius: 6px; }
        .link { color: var(--button-primary-bg); text-decoration: none; display: inline-block; margin-top: 15px; }
    </style>
</head>
<body class="dark-mode">
    <div class="container">
        <h2>{{ title }}</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="flash">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form method="post">
            <label for="email">E-mail</label>
            <input type="email" id="email" name="email" required>
            <label for="password">Contraseña</label>
            <input type="password" id="password" name="password" required>
            <button type="submit" class="btn">{{ title }}</button>
        </form>
        <div style="margin-top: 20px;">
        {% if is_login %}
            <a href="{{ url_for('register') }}" class="link">¿No tienes cuenta? Regístrate aquí</a>
        {% else %}
            <a href="{{ url_for('login') }}" class="link">¿Ya tienes cuenta? Inicia sesión</a>
        {% endif %}
        </div>
    </div>
    <script>
        const currentTheme = localStorage.getItem('theme');
        if (currentTheme === 'light') document.body.classList.remove('dark-mode');
    </script>
</body>
</html>
"""

# Plantilla para editar la redirección con el mismo estilo y modo oscuro
EDIT_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar redirección</title>
    <style>
        :root {
            --bg-color: #f0f2f5;
            --container-bg: white;
            --text-color: #333;
            --label-color: #555;
            --input-bg: white;
            --input-border: #ccc;
            --button-primary-bg: #007bff;
            --button-primary-hover-bg: #0056b3;
            --button-secondary-bg: #6c757d;
            --button-secondary-hover-bg: #5a6268;
            --box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .dark-mode {
            --bg-color: #1a1a1a;
            --container-bg: #242424;
            --text-color: #f8f8f8;
            --label-color: #cccccc;
            --input-bg: #333333;
            --input-border: #555555;
            --button-primary-bg: #2979ff;
            --button-primary-hover-bg: #1565c0;
            --button-secondary-bg: #555;
            --button-secondary-hover-bg: #444;
            --box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background-color: var(--bg-color);
            transition: background-color 0.3s ease;
        }
        .container {
            background: var(--container-bg);
            padding: 40px;
            border-radius: 12px;
            box-shadow: var(--box-shadow);
            width: 90%;
            max-width: 500px;
        }
        label {
            display: block;
            margin-bottom: 10px;
            color: var(--label-color);
        }
        input[type="text"] {
            width: calc(100% - 24px);
            padding: 12px;
            border: 1px solid var(--input-border);
            border-radius: 6px;
            background: var(--input-bg);
            color: var(--text-color);
        }
        .button-group {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 20px;
        }
        .btn {
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
        }
        .btn-primary { background-color: var(--button-primary-bg); }
        .btn-primary:hover { background-color: var(--button-primary-hover-bg); }
        .btn-secondary { background-color: var(--button-secondary-bg); }
        .btn-secondary:hover { background-color: var(--button-secondary-hover-bg); }
        .theme-switch-wrapper {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            margin-bottom: 20px;
        }
        .theme-switch { position: relative; display: inline-block; width: 60px; height: 34px; }
        .theme-switch input { display:none; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 34px; }
        .slider:before { position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: #fff; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #2196F3; }
        input:checked + .slider:before { transform: translateX(26px); }
    </style>
</head>
<body>
    <div class="container">
        <div class="theme-switch-wrapper">
            <label class="theme-switch" for="checkbox">
                <input type="checkbox" id="checkbox" />
                <div class="slider round"></div>
            </label>
        </div>
        <h2 style="margin-top:0; color: var(--text-color);">Editar redirección</h2>
        <form method="post">
            <label for="data">Nueva dirección:</label>
            <input type="text" id="data" name="data" value="{{ data }}" required>
            <div class="button-group">
                <button type="submit" class="btn btn-primary">Guardar</button>
                <a href="{{ url_for('index', qr_id=qr_id) }}" class="btn btn-secondary">Volver</a>
            </div>
        </form>
    </div>
    <script>
        const themeToggle = document.getElementById('checkbox');
        const body = document.body;
        const currentTheme = localStorage.getItem('theme');
        if (currentTheme === 'dark' || !currentTheme) {
            body.classList.add('dark-mode');
            themeToggle.checked = true;
        }
        themeToggle.addEventListener('change', () => {
            if (themeToggle.checked) {
                body.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark');
            } else {
                body.classList.remove('dark-mode');
                localStorage.setItem('theme', 'light');
            }
        });
    </script>
</body>
</html>
"""

# --- RUTAS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.')
            return redirect(url_for('login'))
    return render_template_string(AUTH_TEMPLATE, title='Iniciar Sesión', is_login=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('register'))
        user = User.query.filter_by(email=email).first()
        if user:
            flash('El email ya está registrado.')
            return redirect(url_for('register'))
        else:
            new_user = User(email=email, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
    return render_template_string(AUTH_TEMPLATE, title='Crear Cuenta', is_login=False)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    qr_image_base64 = None
    
    # Cargar diseños del usuario activo
    user_designs = Design.query.filter_by(user_id=current_user.id).all()
    designs = {d.name: {'fill_color': d.fill_color, 'back_color': d.back_color, 'logo_base64': d.logo_base64} for d in user_designs}
    
    data = request.form.get('data', '')
    fill_color = request.form.get('fill_color', '#000000')
    back_color = request.form.get('back_color', '#ffffff')
    logo_base64 = request.form.get('logo_base64')
    dynamic = bool(request.form.get('dynamic'))
    dynamic_id = request.args.get('qr_id')

    if dynamic_id and request.method == 'GET':
        qr_obj = DynamicQR.query.filter_by(id=dynamic_id, user_id=current_user.id).first()
        if qr_obj:
            data = qr_obj.data
            fill_color = qr_obj.fill_color
            back_color = qr_obj.back_color
            logo_base64 = qr_obj.logo_base64
            qr_content = url_for('redirect_dynamic', qr_id=dynamic_id, _external=True)
            img_buffer = generate_qr_with_logo(qr_content, fill_color, back_color, logo_base64)
            qr_image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            dynamic = True

    if request.method == 'POST':
        if not data:
            return render_template_string(HMTL_TEMPLATE, error="Por favor, introduce datos.")

        logo_base64 = request.form.get('logo_base64')
        qr_content = data
        if dynamic:
            dynamic_id = str(uuid.uuid4())
            new_qr = DynamicQR(
                id=dynamic_id,
                user_id=current_user.id,
                data=data,
                fill_color=fill_color,
                back_color=back_color,
                logo_base64=logo_base64
            )
            db.session.add(new_qr)
            db.session.commit()
            qr_content = url_for('redirect_dynamic', qr_id=dynamic_id, _external=True)

        img_buffer = generate_qr_with_logo(qr_content, fill_color, back_color, logo_base64)
        qr_image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    return render_template_string(
        HMTL_TEMPLATE,
        qr_image=qr_image_base64,
        data=data,
        fill_color=fill_color,
        back_color=back_color,
        logo_base64=logo_base64,
        dynamic_id=dynamic_id,
        dynamic=dynamic,
        designs=designs,
        designs_json=json.dumps(designs),
    )

def generate_qr_with_logo(data, fill_color, back_color, logo_base64=None):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')

    if logo_base64 and 'base64,' in logo_base64:
        header, encoded = logo_base64.split(',', 1)
        logo_data = base64.b64decode(encoded)
        logo_image = Image.open(io.BytesIO(logo_data)).convert('RGBA')

        qr_width, qr_height = img_qr.size
        max_logo_size = qr_width // 4
        logo_image.thumbnail((max_logo_size, max_logo_size))

        logo_pos = ((qr_width - logo_image.width) // 2, (qr_height - logo_image.height) // 2)
        img_qr.paste(logo_image, logo_pos, mask=logo_image)

    buf = io.BytesIO()
    img_qr.save(buf, 'PNG')
    buf.seek(0)
    return buf


@app.route('/save_design', methods=['POST'])
@login_required
def save_design():
    name = request.form.get('name')
    if not name:
        return 'Nombre requerido', 400
    
    design = Design.query.filter_by(name=name, user_id=current_user.id).first()
    if not design:
        design = Design(name=name, user_id=current_user.id)
        db.session.add(design)
    
    design.fill_color = request.form.get('fill_color', '#000000')
    design.back_color = request.form.get('back_color', '#ffffff')
    design.logo_base64 = request.form.get('logo_base64')
    db.session.commit()
    
    return 'ok'


@app.route('/r/<qr_id>')
def redirect_dynamic(qr_id):
    # Esta ruta sigue siendo publica, ya que es la que se escanea en la red
    qr_obj = DynamicQR.query.filter_by(id=qr_id).first()
    if not qr_obj:
        return 'Código QR no encontrado', 404
        
    data = qr_obj.data
    if data.startswith('http://') or data.startswith('https://'):
        return redirect(data)
    return data


@app.route('/edit/<qr_id>', methods=['GET', 'POST'])
@login_required
def edit_dynamic(qr_id):
    qr_obj = DynamicQR.query.filter_by(id=qr_id, user_id=current_user.id).first()
    if not qr_obj:
        return 'Código QR no encontrado o no tienes permiso para editarlo', 404
        
    if request.method == 'POST':
        new_data = request.form.get('data', '')
        qr_obj.data = new_data
        db.session.commit()
        return redirect(url_for('index', qr_id=qr_id))
        
    return render_template_string(EDIT_TEMPLATE, data=qr_obj.data, qr_id=qr_id)


# --- Migracion Inicial (solo se ejecuta la primera vez) ---
def run_migrations():
    db.create_all()
    if os.path.exists('dynamic_qrs.json') and not User.query.first():
        mig_user = User(email="migracion@localhost", password_hash=generate_password_hash("secreto123"))
        db.session.add(mig_user)
        db.session.commit()
        
        with open('dynamic_qrs.json', 'r') as f:
            qrs = json.load(f)
            for k, v in qrs.items():
                if isinstance(v, dict):
                    qr = DynamicQR(id=k, user_id=mig_user.id, data=v.get('data'), fill_color=v.get('fill_color', '#000000'), back_color=v.get('back_color', '#ffffff'), logo_base64=v.get('logo_base64'))
                else:
                    qr = DynamicQR(id=k, user_id=mig_user.id, data=v)
                db.session.add(qr)
        
        if os.path.exists('qr_designs.json'):
            with open('qr_designs.json', 'r') as f:
                ds = json.load(f)
                for name, v in ds.items():
                    d = Design(user_id=mig_user.id, name=name, fill_color=v.get('fill_color'), back_color=v.get('back_color'), logo_base64=v.get('logo_base64'))
                    db.session.add(d)
        
        db.session.commit()

with app.app_context():
    run_migrations()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
