"""
Harmonia Backend v4.0 (Cloud SQL + GCS)
- PostgreSQL (Cloud SQL) 기반 21만 곡 검색
- GCS 기반 MIDI 스트리밍
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os, json, urllib.parse

PORT = int(os.environ.get('PORT', 8080))
BUCKET_NAME = os.environ.get('GCS_BUCKET', 'harmonia-midi')

# Cloud SQL 접속 정보 (환경변수 우선, 없으면 기본값)
DB_HOST = os.environ.get('DB_HOST', '/cloudsql/harmonia-489109:asia-northeast3:harmonia-db')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', '')
DB_NAME = os.environ.get('DB_NAME', 'postgres')

def get_db():
    import psycopg2
    # Cloud Run에서는 Unix socket, 외부에서는 TCP
    if DB_HOST.startswith('/cloudsql/'):
        return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
    else:
        return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME, port=5432)

class HarmoniaHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # API: Search
        if self.path.startswith('/api/search'):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q', [''])[0]
            self.json_response(self.search_db(query))
            return

        # API: Channel
        if self.path.startswith('/api/channel'):
            channel_id = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('id', [''])[0]
            self.json_response(self.get_channel_songs(channel_id))
            return

        # API: Stream MIDI from GCS (redirect to public URL)
        if self.path.startswith('/api/stream'):
            track_id = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('id', [''])[0]
            self.stream_midi(track_id)
            return

        # API: Health check
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            return

        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        return super().do_GET()

    def json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def search_db(self, query):
        if len(query) < 2: return []
        try:
            conn = get_db()
            cur = conn.cursor()
            q = f"%{query}%"
            cur.execute("""SELECT id, title, composer, dataset, era, tags, license_type, license_summary 
                          FROM tracks 
                          WHERE title ILIKE %s OR composer ILIKE %s OR tags ILIKE %s
                          LIMIT 100""", (q, q, q))
            rows = cur.fetchall()
            conn.close()
            return [{"id": r[0], "title": r[1], "composer": r[2], "dataset": r[3], "era": r[4], "tags": r[5], "license": r[6], "license_text": r[7]} for r in rows]
        except Exception as e:
            import traceback
            print(f"🚨 Search error: {e}")
            traceback.print_exc()
            return [{"error": str(e)}]

    def get_channel_songs(self, channel_id):
        try:
            conn = get_db()
            cur = conn.cursor()
            if channel_id == 'classical':
                cur.execute("SELECT id, title, composer, dataset, era, tags, license_type, license_summary FROM tracks WHERE dataset = 'mutopia_midi' ORDER BY title LIMIT 100")
            elif channel_id == 'korean_master':
                cur.execute("SELECT id, title, composer, dataset, era, tags, license_type, license_summary FROM tracks WHERE dataset = 'korean_jeongganbo' ORDER BY title LIMIT 100")
            elif channel_id == 'piano_healing':
                cur.execute("SELECT id, title, composer, dataset, era, tags, license_type, license_summary FROM tracks WHERE dataset = 'adl-piano-midi' ORDER BY title LIMIT 100")
            elif channel_id == 'world_folk':
                cur.execute("SELECT id, title, composer, dataset, era, tags, license_type, license_summary FROM tracks WHERE dataset = 'historical_world' ORDER BY title LIMIT 100")
            else:
                cur.execute("SELECT id, title, composer, dataset, era, tags, license_type, license_summary FROM tracks ORDER BY RANDOM() LIMIT 100")
            rows = cur.fetchall()
            conn.close()
            return [{"id": r[0], "title": r[1], "composer": r[2], "dataset": r[3], "era": r[4], "tags": r[5], "license": r[6], "license_text": r[7]} for r in rows]
        except Exception as e:
            print(f"Channel error: {e}")
            return []

    def stream_midi(self, track_id):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('SELECT path FROM tracks WHERE id = %s', (track_id,))
            row = cur.fetchone()
            conn.close()
            
            if row:
                # GCS 공개 URL로 리다이렉트
                gcs_url = f"https://storage.googleapis.com/{BUCKET_NAME}/datasets/{row[0]}"
                self.send_response(302)
                self.send_header('Location', gcs_url)
                self.end_headers()
            else:
                self.send_error(404)
        except Exception as e:
            print(f"Stream error: {e}")
            self.send_error(500)

if __name__ == '__main__':
    print(f"🎵 Harmonia v4.0 (Cloud SQL + GCS) on port {PORT}")
    HTTPServer(('0.0.0.0', PORT), HarmoniaHandler).serve_forever()
