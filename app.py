from flask import Flask, request, render_template_string
import qrcode
from PIL import Image
import io
import base64

app = Flask(__name__)

# Plantilla HTML actualizada con campo para subir logo
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador de Código QR con Logo</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background-color: #f0f2f5; }
        .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; width: 90%; max-width: 500px; }
        h1 { color: #333; }
        label { font-weight: 500; color: #555; display: block; margin: 15px 0 5px; }
        input[type="text"], input[type="file"] { width: calc(100% - 24px); padding: 12px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }
        input[type="file"] { background-color: #f9f9f9; }
        .color-selectors { display: flex; justify-content: center; gap: 20px; margin: 10px 0; }
        .color-selectors div { display: flex; flex-direction: column; align-items: center; }
        input[type="color"] { width: 50px; height: 50px; border: none; border-radius: 8px; cursor: pointer; }
        input[type="submit"], .download-btn { background-color: #007bff; color: white; padding: 12px 25px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; text-decoration: none; display: inline-block; margin-top: 10px; }
        input[type="submit"]:hover, .download-btn:hover { background-color: #0056b3; }
        .qr-container { margin-top: 25px; }
        img { border: 1px solid #eee; border-radius: 8px; max-width: 100%; height: auto; }
        .download-btn { background-color: #28a745; }
        .download-btn:hover { background-color: #218838; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Generador de Código QR con Logo</h1>
        <form action="/" method="post" enctype="multipart/form-data">
            <label for="data">Introduce el texto o URL:</label>
            <input type="text" id="data" name="data" value="{{ data or '' }}" required>
            
            <div class="color-selectors">
                <div>
                    <label for="fill_color">Color del QR:</label>
                    <input type="color" id="fill_color" name="fill_color" value="{{ fill_color or '#000000' }}">
                </div>
                <div>
                    <label for="back_color">Color de fondo:</label>
                    <input type="color" id="back_color" name="back_color" value="{{ back_color or '#ffffff' }}">
                </div>
            </div>
            
            <!-- Nuevo: campo para subir el logo -->
            <label for="logo">Logo (opcional):</label>
            <input type="file" id="logo" name="logo" accept="image/*">
            
            <input type="submit" value="Generar QR">
        </form>
        
        {% if qr_image %}
            <div class="qr-container">
                <h2>Tu Código QR:</h2>
                <img src="data:image/png;base64,{{ qr_image }}" alt="Código QR Generado">
                <!-- El botón de descarga ahora usa la imagen en Base64 directamente -->
                <a href="data:image/png;base64,{{ qr_image }}" class="download-btn" download="codigo_qr_con_logo.png">Descargar QR</a>
            </div>
        {% endif %}
    </div>
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
            return render_template_string(HTML_TEMPLATE, error="Por favor, introduce datos para generar el QR.")

        logo_file = request.files.get('logo')
        
        # Generar la imagen del QR
        img_buffer = generate_qr_with_logo(data, fill_color, back_color, logo_file)
        
        # Codificar la imagen en Base64 para mostrarla en la web
        qr_image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    return render_template_string(HTML_TEMPLATE, 
                                  qr_image=qr_image_base64, 
                                  data=data,
                                  fill_color=fill_color,
                                  back_color=back_color)

def generate_qr_with_logo(data, fill_color, back_color, logo_file=None):
    """Genera un código QR, opcionalmente con un logo en el centro."""
    # CRÍTICO: Aumentar la corrección de errores a 'H' (High) para asegurar que el QR sea legible con un logo encima.
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Crea la imagen del QR y la convierte a RGBA para poder pegar otra imagen con transparencia.
    img_qr = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')

    if logo_file and logo_file.filename != '':
        # Abre el logo y lo convierte a RGBA
        logo = Image.open(logo_file.stream).convert('RGBA')

        # Calcula el tamaño máximo que puede tener el logo (aprox. 25-30% del tamaño del QR)
        qr_width, qr_height = img_qr.size
        max_logo_size = qr_width // 4
        
        # Redimensiona el logo manteniendo su proporción
        logo.thumbnail((max_logo_size, max_logo_size))

        # Calcula la posición para centrar el logo
        logo_pos = ((qr_width - logo.width) // 2, (qr_height - logo.height) // 2)

        # Pega el logo en el QR. La máscara se usa para manejar la transparencia del logo.
        img_qr.paste(logo, logo_pos, mask=logo)

    # Guarda la imagen final en un buffer de memoria
    buf = io.BytesIO()
    img_qr.save(buf, 'PNG')
    buf.seek(0)
    
    return buf

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
