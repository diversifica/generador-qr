# Generador de Códigos QR

Una aplicación web simple y moderna construida con Flask para generar códigos QR personalizados. Permite a los usuarios crear códigos QR a partir de texto o URLs, personalizar sus colores, añadir logos y descargarlos fácilmente.

## ✨ Funcionalidades

-   **Generación de QR:** Crea códigos QR a partir de cualquier texto o URL.
-   **Personalización de Color:** Elige el color de los módulos del QR y el color del fondo usando selectores de color intuitivos.
-   **Previsualización Integrada:** El código QR generado se muestra instantáneamente en la misma página.
-   **Descarga Fácil:** Descarga el código QR resultante como un archivo de imagen PNG con un solo clic.
-   **Soporte de Logo:** Añade una imagen de logo personalizada en el centro del código QR.
-   **Recorte de Logo Integrado:** Herramienta de recorte de imágenes (Cropper.js) para asegurar que el logo se ajuste perfectamente y en formato cuadrado.
-   **Botón "Nuevo QR":** Limpia el formulario y oculta el QR generado para facilitar la creación de nuevos códigos.
-   **Experiencia de Usuario Mejorada:** Se ha corregido el "salto" de la interfaz al mostrar el QR y el botón de descarga, asegurando una experiencia fluida.
-   **Interfaz Limpia:** Diseño de usuario sencillo, moderno y responsivo.
-   **Contenerización:** Incluye un `Dockerfile` para un despliegue rápido y consistente usando Docker.

## 🛠️ Tecnologías Utilizadas

-   **Backend:** Python 3.9+
-   **Framework:** Flask
-   **Generación de QR:** `qrcode` y `Pillow`
-   **Servidor WSGI:** Gunicorn
-   **Frontend:** HTML5, CSS3, JavaScript
-   **Recorte de Imagen:** Cropper.js
-   **Contenerización:** Docker

## 🚀 Cómo Empezar

Puedes ejecutar este proyecto de dos maneras: usando Docker (recomendado para un despliegue fácil) o localmente en tu máquina (ideal para desarrollo).

### Opción 1: Usando Docker (Recomendado)

**Requisitos:**
-   [Docker](https://www.docker.com/get-started) instalado en tu sistema.

**Pasos:**

1.  **Clona el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd generador-qr
    ```

2.  **Construye la imagen de Docker:**
    Este comando leerá el `Dockerfile` y creará una imagen con todas las dependencias y la aplicación lista para ejecutarse.
    ```bash
    docker build -t generador-qr .
    ```

3.  **Ejecuta el contenedor:**
    Este comando iniciará un contenedor a partir de la imagen que acabas de crear, mapeando el puerto 5000 del contenedor al puerto 5000 de tu máquina.
    ```bash
    docker run -d -p 5000:5000 --name mi-generador-qr generador-qr
    ```

4.  **¡Listo!**
    Abre tu navegador y visita [http://localhost:5000](http://localhost:5000) para usar la aplicación.

### Opción 2: Ejecución Local (Para Desarrollo)

**Requisitos:**
-   Python 3.9 o superior.
-   `pip` (el gestor de paquetes de Python).

**Pasos:**

1.  **Clona el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd generador-qr
    ```

2.  **Crea y activa un entorno virtual:**
    Es una buena práctica para aislar las dependencias del proyecto.
    ```bash
    # En Windows
    python -m venv venv
    venv\Scripts\activate

    # En macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecuta la aplicación Flask:**
    ```bash
    python app.py
    ```

5.  **¡Listo!**
    Abre tu navegador y visita [http://localhost:5000](http://localhost:5000).

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.