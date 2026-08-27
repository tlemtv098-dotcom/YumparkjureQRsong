FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate --noinput || true
EXPOSE 8000
CMD ["gunicorn", "yum_jukebox.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
