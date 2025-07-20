from flask import Flask, request, render_template_string
import qrcode
from PIL import Image
import io
import base64

app = Flask(__name__)

# --- Plantilla HTML actualizada con Cropper.js, Modal y Modo Oscuro ---
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
            <h1>Generador de Código QR con Logo</h1>
            <div class="theme-switch-wrapper">
                <label class="theme-switch" for="checkbox">
                    <input type="checkbox" id="checkbox" />
                    <div class="slider round"></div>
                </label>
                <span style="margin-left: 10px; color: var(--label-color);">Modo Oscuro</span>
            </div>
        </div>
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
                <a href="data:image/png;base64,{{ qr_image }}" class="btn btn-success download-btn" download="codigo_qr.png" id="actual-download-button">Descargar QR</a>
            {% endif %}
        </div>
    </div>

    <!-- Modal para recortar la imagen -->
    <div id="crop-modal">
        <div id="crop-container">
            <h2>Recortar Logo</h2>
            <div><img id="image-to-crop"></div>
            <button type="button" id="crop-button" class="btn btn-primary">Confirmar Recorte</button>
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
            const newDownloadLink = tempDiv.querySelector('.qr-container a')?.href;

            if (newQrImageSrc) {
                // Actualizar la imagen y el botón de descarga en la página actual
                qrContainer.innerHTML = `
                    <h2>Tu Código QR:</h2>
                    <img src="${newQrImageSrc}" alt="Código QR Generado">
                    <a href="${newDownloadLink}" class="btn btn-success download-btn" download="codigo_qr.png" id="actual-download-button">Descargar QR</a>
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


