from flask import Flask, request, send_file, render_template_string
import qrcode
import io

app = Flask(__name__)

# Template HTML simple para el formulario
HTML_FORM = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador de Código QR</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background-color: #f4f4f4; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        input[type="text"] { width: 80%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
        input[type="submit"] { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        input[type="submit"]:hover { background-color: #0056b3; }
        img { margin-top: 20px; border: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Generador de Código QR</h1>
        <form action="/generate_qr" method="post">
            <label for="data">Introduce el texto o URL:</label><br>
            <input type="text" id="data" name="data" required><br>
            <input type="submit" value="Generar QR">
        </form>
        {% if qr_image %}
            <h2>Tu Código QR:</h2>
            <img src="data:image/png;base64,{{ qr_image }}" alt="Código QR">
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_FORM)

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.form.get('data')
    if not data:
        return "Por favor, introduce datos para generar el QR.", 400

    # Crear objeto QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar la imagen en un buffer de memoria
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0) # Volver al inicio del buffer

    # Enviar la imagen como respuesta
    return send_file(buf, mimetype="image/png")

# Ruta para mostrar el QR generado directamente en la página con el formulario
@app.route('/show_qr', methods=['GET'])
def show_qr():
    data = request.args.get('data')
    if not data:
        return "No se proporcionaron datos para mostrar el QR.", 400

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    import base64
    qr_image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template_string(HTML_FORM, qr_image=qr_image_base64)


if __name__ == '__main__':
    # Usamos 0.0.0.0 para que sea accesible desde fuera del contenedor
    app.run(host='0.0.0.0', port=5000, debug=True)