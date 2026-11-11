import os, time, string, random
import psycopg2, redis
from flask import Flask, request, redirect
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
REQS = Counter('http_requests_total', 'Total requests', ['endpoint'])
cache = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, decode_responses=True)

def db():
    return psycopg2.connect(host=os.getenv('DB_HOST', 'db'), dbname=os.getenv('DB_NAME', 'urls'),
                            user=os.getenv('DB_USER', 'app'), password=os.getenv('DB_PASSWORD'))

def run(query, params=(), fetch=False):
    conn = db()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone() if fetch else None
    finally:
        conn.close()

for _ in range(15):
    try:
        run('CREATE TABLE IF NOT EXISTS urls (code TEXT PRIMARY KEY, url TEXT NOT NULL)')
        break
    except Exception:
        time.sleep(2)

@app.route('/health')
def health():
    return {'status': 'ok'}

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/shorten', methods=['POST'])
def shorten():
    REQS.labels('shorten').inc()
    url = (request.get_json(silent=True) or {}).get('url')
    if not url:
        return {'error': 'url required'}, 400
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    run('INSERT INTO urls (code, url) VALUES (%s, %s)', (code, url))
    cache.set(code, url, ex=3600)
    return {'code': code}, 201

@app.route('/<code>')
def go(code):
    REQS.labels('redirect').inc()
    url = cache.get(code)
    if not url:
        row = run('SELECT url FROM urls WHERE code = %s', (code,), fetch=True)
        if not row:
            return {'error': 'not found'}, 404
        url = row[0]
        cache.set(code, url, ex=3600)
    return redirect(url)
