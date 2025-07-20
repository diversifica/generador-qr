from flask import Flask, request, send_file, render_template_string
import qrcode
import io
import base64

app = Flask(__name__)

# Plantilla HTML mejorada con selectores de color y botón de descarga
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador de Código QR Avanzado</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background-color: #f0f2f5; }
        .container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; width: 90%; max-width: 500px; }
        h1 { color: #333; }
        label { font-weight: 500; color: #555; display: block; margin: 15px 0 5px; }
        input[type="text"] { width: calc(100% - 24px); padding: 12px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }
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
        <h1>Generador de Código QR</h1>
        <form action="/" method="post">
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
            
            <input type="submit" value="Generar QR">
        </form>
        
        {% if qr_image %}
            <div class="qr-container">
                <h2>Tu Código QR:</h2>
                <img src="data:image/png;base64,{{ qr_image }}" alt="Código QR Generado">
                <a href="{{ download_link }}" class="download-btn" download="codigo_qr.png">Descargar QR</a>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.form.get('data')
        fill_color = request.form.get('fill_color', 'black')
        back_color = request.form.get('back_color', 'white')

        if not data:
            # Renderiza la plantilla con un mensaje de error si no hay datos
            return render_template_string(HTML_TEMPLATE, error="Por favor, introduce datos para generar el QR.")

        # Generar la imagen del QR
        img_buffer, _ = generate_qr_image(data, fill_color, back_color)
        
        # Codificar la imagen en Base64 para mostrarla en la web
        qr_image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # Crear el enlace de descarga con los parámetros
        download_link = f"/download?data={data}&fill_color={fill_color.lstrip('#')}&back_color={back_color.lstrip('#')}"

        return render_template_string(HTML_TEMPLATE, 
                                      qr_image=qr_image_base64, 
                                      download_link=download_link,
                                      data=data,
                                      fill_color=fill_color,
                                      back_color=back_color)
    
    # Para peticiones GET, simplemente muestra el formulario
    return render_template_string(HTML_TEMPLATE)

@app.route('/download')
def download_qr():
    data = request.args.get('data')
    fill_color = '#' + request.args.get('fill_color', '000000')
    back_color = '#' + request.args.get('back_color', 'ffffff')

    if not data:
        return "Datos no proporcionados.", 400

    # Generar la imagen del QR
    img_buffer, img = generate_qr_image(data, fill_color, back_color)

    # Enviar la imagen como un archivo para descargar
    return send_file(
        img_buffer,
        mimetype='image/png',
        as_attachment=True,
        download_name='codigo_qr.png'
    )

def generate_qr_image(data, fill_color, back_color):
    """Genera una imagen de código QR y la devuelve como un buffer de memoria."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    
    return buf, img

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
