# Imagen base de Python
FROM python:3.10-slim

# Crear carpeta para el proyecto
WORKDIR /app

# Copiar los archivos del proyecto al contenedor
COPY . /app

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Puerto donde corre la app
EXPOSE 5000

# Comando para iniciar Flask con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
