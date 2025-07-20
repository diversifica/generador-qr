from flask import Flask, request, render_template_string
import qrcode
from PIL import Image
import io
import base64

app = Flask(__name__)

# --- Plantilla HTML actualizada con Cropper.js y Modal ---
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
            --bg-color: #2c2c2c;
            --container-bg: #3a3a3a;
            --text-color: #f0f0f0;
            --label-color: #e0e0e0;
            --input-bg: #4a4a4a;
            --input-border: #666;
            --button-primary-bg: #4a90e2;
            --button-primary-hover-bg: #357bd8;
            --button-secondary-bg: #555;
            --button-secondary-hover-bg: #444;
            --button-success-bg: #4CAF50;
            --button-success-hover-bg: #45a049;
            --box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }

        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background-color: var(--bg-color); transition: background-color 0.3s ease; }
        .container { background: var(--container-bg); padding: 40px; border-radius: 12px; box-shadow: var(--box-shadow); text-align: center; width: 90%; max-width: 500px; transition: background-color 0.3s ease, box-shadow 0.3s ease; }
        h1 { color: var(--text-color); transition: color 0.3s ease; }
        label { font-weight: 500; color: var(--label-color); display: block; margin: 15px 0 5px; transition: color 0.3s ease; }
        input[type="text"], input[type="file"] { width: calc(100% - 24px); padding: 12px; margin-bottom: 10px; border: 1px solid var(--input-border); border-radius: 6px; font-size: 16px; background-color: var(--input-bg); color: var(--text-color); transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease; }
        .color-selectors { display: flex; justify-content: center; gap: 20px; margin: 10px 0; }
        input[type="color"] { width: 50px; height: 50px; border: none; border-radius: 8px; cursor: pointer; }
        input[type="submit"], .download-btn, #crop-button, #new-qr-button { color: white; padding: 12px 25px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; text-decoration: none; display: inline-block; margin-top: 10px; margin-left: 5px; margin-right: 5px; transition: background-color 0.3s ease; }
        input[type="submit"], #crop-button { background-color: var(--button-primary-bg); }
        input[type="submit"]:hover, #crop-button:hover { background-color: var(--button-primary-hover-bg); }
        .download-btn { background-color: var(--button-success-bg); }
        .download-btn:hover { background-color: var(--button-success-hover-bg); }
        #new-qr-button { background-color: var(--button-secondary-bg); }
        #new-qr-button:hover { background-color: var(--button-secondary-hover-bg); }

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
            margin-bottom: 20px;
            width: 100%;
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
        <div class="theme-switch-wrapper">
            <label class="theme-switch" for="checkbox">
                <input type="checkbox" id="checkbox" />
                <div class="slider round"></div>
            </label>
            <em style="margin-left: 10px; color: var(--label-color);">Modo Oscuro</em>
        </div>
        <h1>Generador de Código QR con Logo</h1>
        <form action="/" method="post" enctype="multipart/form-data" id="qr-form">
            <label for="data">Introduce el texto o URL:</label>
            <input type="text" id="data" name="data" value="{{ data or '' }}" required>
            <div class="color-selectors">
                <div><label for="fill_color">Color QR:</label><input type="color" id="fill_color" name="fill_color" value="{{ fill_color or '#000000' }}"></div>
                <div><label for="back_color">Fondo:</label><input type="color" id="back_color" name="back_color" value="{{ back_color or '#ffffff' }}"></div>
            </div>
            <label for="logo-input">Logo (opcional, se recortará a formato cuadrado):</label>
            <input type="file" id="logo-input" accept="image/*">
            <!-- Campo oculto para guardar la imagen recortada en Base64 -->
            <input type="hidden" id="logo_base64" name="logo_base64">
            <input type="submit" value="Generar QR">
            <button type="button" id="new-qr-button">Nuevo QR</button>
        </form>
        <div class="qr-container" style="{% if not qr_image %}display: none;{% endif %}">
            {% if qr_image %}
                <h2>Tu Código QR:</h2>
                <img src="data:image/png;base64,{{ qr_image }}" alt="Código QR Generado">
                <a href="data:image/png;base64,{{ qr_image }}" class="download-btn" download="codigo_qr.png">Descargar QR</a>
            {% endif %}
        </div>
    </div>

    <!-- Modal para recortar la imagen -->
    <div id="crop-modal">
        <div id="crop-container">
            <h2>Recortar Logo</h2>
            <div><img id="image-to-crop"></div>
            <button type="button" id="crop-button">Confirmar Recorte</button>
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
        const qrContainer = document.querySelector('.qr-container');
        const themeToggle = document.getElementById('checkbox');
        const body = document.body;

        let cropper;

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
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    qr_image_base64 = None
    data = request.form.get('data', '')
    fill_color = request.form.get('fill_color', '#000000')
    back_color = request.form.get('back_color', '#ffffff')

    if request.method == 'POST':
        if not data:
            return render_template_string(HMTL_TEMPLATE, error="Por favor, introduce datos.")

        # --- Lógica del Backend actualizada ---
        # Ahora recibimos una cadena Base64 en lugar de un archivo.
        logo_base64 = request.form.get('logo_base64')
        
        img_buffer = generate_qr_with_logo(data, fill_color, back_color, logo_base64)
        
        qr_image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    return render_template_string(HMTL_TEMPLATE, 
                                  qr_image=qr_image_base64, 
                                  data=data,
                                  fill_color=fill_color,
                                  back_color=back_color)

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

    # Si se envió un logo en Base64, lo procesamos.
    if logo_base64 and 'base64,' in logo_base64:
        # Decodificar la cadena Base64 para obtener los bytes de la imagen
        header, encoded = logo_base64.split(',', 1)
        logo_data = base64.b64decode(encoded)
        logo_image = Image.open(io.BytesIO(logo_data)).convert('RGBA')

        qr_width, qr_height = img_qr.size
        max_logo_size = qr_width // 4
        logo_image.thumbnail((max_logo_size, max_logo_size))

        logo_pos = ((qr_width - logo_image.width) // 2, (qr_height - logo_image.height) // 2)
        
        # Pegar el logo recortado
        img_qr.paste(logo_image, logo_pos, mask=logo_image)

    buf = io.BytesIO()
    img_qr.save(buf, 'PNG')
    buf.seek(0)
    return buf

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


