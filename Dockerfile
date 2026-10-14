FROM python:3.12-slim

WORKDIR /app

# Build-time environment variables (needed for collectstatic)
ENV SECRET_KEY=build-time-secret-key-for-collectstatic-only
ENV DEBUG=False
ENV DATABASE_URL=sqlite:///tmp/build.db

# Dependencies first so the layer caches across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

# The container must listen on the port Render assigns, which it passes in the
# PORT environment variable. docker-entrypoint.sh runs migrate, then
# ensure_admin, then execs gunicorn on that port.
EXPOSE 8000
CMD ["/bin/sh", "docker-entrypoint.sh"]
