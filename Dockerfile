# Usa una imagen base de Python oficial.
# Te recomiendo usar una versión específica, por ejemplo, python:3.9-slim-buster
# para un tamaño de imagen más pequeño.
FROM python:3.9-slim-buster

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos al directorio de trabajo
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos de tu aplicación al directorio de trabajo
COPY . .

# Expone el puerto en el que la aplicación Flask se ejecutará
EXPOSE 5000

# Comando para ejecutar la aplicación Flask cuando el contenedor se inicie
# Usa Gunicorn para producción; para desarrollo puedes usar "flask run"
# Pero para EasyPanel y despliegues robustos, Gunicorn es preferible.
# Si solo usas "flask run", el comando sería: CMD ["python", "app.py"]
# Para Gunicorn:
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]