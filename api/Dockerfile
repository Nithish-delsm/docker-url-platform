FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
RUN useradd -m appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app.py .
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s CMD python -c "import urllib.request as u; u.urlopen('http://localhost:5000/health')" || exit 1
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "1", "--threads", "4", "app:app"]
