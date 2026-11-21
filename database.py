"""SQLite-first persistence layer; no database server is required for local use."""
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        if Config.DATABASE_TYPE != 'sqlite':
            raise RuntimeError('This PyCharm-ready build uses SQLite. Set DATABASE_TYPE=sqlite, or configure MySQL separately.')
        self.db_path = Path(Config.DATABASE_URL)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                source TEXT,
                url TEXT UNIQUE,
                published_date TEXT,
                scraped_date TEXT DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                severity TEXT,
                keywords TEXT,
                india_related INTEGER DEFAULT 0,
                raw_content TEXT
            )''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON threats(category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_severity ON threats(severity)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_india ON threats(india_related)')

    @staticmethod
    def _serialize(row):
        item = dict(row)
        try:
            item['keywords'] = json.loads(item.get('keywords') or '[]')
        except (TypeError, ValueError):
            item['keywords'] = []
        item['india_related'] = bool(item.get('india_related'))
        return item

    def threat_exists(self, url):
        if not url:
            return False
        with self.get_connection() as conn:
            return conn.execute('SELECT 1 FROM threats WHERE url=? LIMIT 1', (url,)).fetchone() is not None

    def add_threat(self, threat_data):
        published = threat_data.get('published_date')
        if isinstance(published, datetime):
            published = published.isoformat()
        elif not published:
            published = datetime.now().isoformat()
        try:
            with self.get_connection() as conn:
                cur = conn.execute('''INSERT OR IGNORE INTO threats
                    (title, description, source, url, published_date, category, severity, keywords, india_related, raw_content)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    threat_data.get('title') or 'Untitled threat', threat_data.get('description', ''),
                    threat_data.get('source', ''), threat_data.get('url'), published,
                    threat_data.get('category', 'other'), threat_data.get('severity', 'info'),
                    json.dumps(threat_data.get('keywords', [])), int(bool(threat_data.get('india_related'))),
                    threat_data.get('raw_content', '')
                ))
                return cur.lastrowid if cur.rowcount else None
        except sqlite3.Error:
            logger.exception('Could not save threat')
            return None

    def get_threats(self, limit=50, offset=0, category=None, severity=None, india_only=False, today_only=False):
        sql = 'SELECT * FROM threats WHERE 1=1'
        params = []
        if category:
            sql += ' AND category=?'; params.append(category)
        if severity:
            sql += ' AND severity=?'; params.append(severity)
        if india_only:
            sql += ' AND india_related=1'
        if today_only:
            sql += " AND date(scraped_date)=date('now','localtime')"
        sql += ' ORDER BY scraped_date DESC, id DESC LIMIT ? OFFSET ?'
        params.extend([max(1, min(int(limit), 200)), max(0, int(offset))])
        with self.get_connection() as conn:
            return [self._serialize(r) for r in conn.execute(sql, params).fetchall()]

    def search_threats(self, query):
        term = f'%{query.lower()}%'
        with self.get_connection() as conn:
            rows = conn.execute('''SELECT * FROM threats WHERE lower(title) LIKE ? OR lower(description) LIKE ? OR lower(keywords) LIKE ? ORDER BY scraped_date DESC LIMIT 50''', (term, term, term)).fetchall()
            return [self._serialize(r) for r in rows]

    def get_stats(self):
        with self.get_connection() as conn:
            total = conn.execute('SELECT COUNT(*) FROM threats').fetchone()[0]
            india = conn.execute('SELECT COUNT(*) FROM threats WHERE india_related=1').fetchone()[0]
            today = conn.execute("SELECT COUNT(*) FROM threats WHERE date(scraped_date)=date('now','localtime')").fetchone()[0]
            severity = {r['severity']: r['n'] for r in conn.execute('SELECT severity, COUNT(*) n FROM threats GROUP BY severity')}
            category = {r['category']: r['n'] for r in conn.execute('SELECT category, COUNT(*) n FROM threats GROUP BY category')}
            return {'total_threats': total, 'india_threats': india, 'today_threats': today, 'by_severity': severity, 'by_category': category}

    def remove_duplicate_threats(self):
        with self.get_connection() as conn:
            cur = conn.execute('DELETE FROM threats WHERE id NOT IN (SELECT MIN(id) FROM threats GROUP BY url)')
            return cur.rowcount
