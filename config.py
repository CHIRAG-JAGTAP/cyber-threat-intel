"""Application configuration. Values can be overridden with environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'local-development-key-change-me')
    DATABASE_URL = os.getenv('DATABASE_URL', str(BASE_DIR / 'cyber_threats.db'))
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite').lower()

    # Optional MySQL settings (used only when DATABASE_TYPE=mysql).
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'cyber_threats')

    # AI chat is optional. Add your own key to the environment to enable it.
    CODEWORDS_API_KEY = os.getenv('CODEWORDS_API_KEY', '')
    USE_CODEWORDS_SCRAPING = os.getenv('USE_CODEWORDS_SCRAPING', 'false').lower() == 'true'
    AUTO_SCRAPE_ON_STARTUP = os.getenv('AUTO_SCRAPE_ON_STARTUP', 'false').lower() == 'true'

    NEWS_SOURCES = [
        {'name': 'The Hacker News', 'url': 'https://thehackernews.com/', 'type': 'rss', 'feed_url': 'https://feeds.feedburner.com/TheHackersNews'},
        {'name': 'Cybersecurity News', 'url': 'https://cybersecuritynews.com/', 'type': 'rss', 'feed_url': 'https://cybersecuritynews.com/feed/'},
        {'name': 'Krebs on Security', 'url': 'https://krebsonsecurity.com/', 'type': 'rss', 'feed_url': 'https://krebsonsecurity.com/feed/'},
        {'name': 'Bleeping Computer', 'url': 'https://www.bleepingcomputer.com/', 'type': 'rss', 'feed_url': 'https://www.bleepingcomputer.com/feed/'},
    ]

    THREAT_KEYWORDS = {
        'ransomware': ['ransomware', 'ransom', 'lockbit', 'ryuk', 'wannacry', 'blackcat'],
        'phishing': ['phishing', 'phish', 'spear phishing', 'credential theft', 'fake login'],
        'data_breach': ['data breach', 'data leak', 'database leak', 'exposed records', 'breach'],
        'ddos': ['ddos', 'denial of service', 'dos attack', 'botnet', 'amplification'],
        'malware': ['malware', 'trojan', 'virus', 'spyware', 'adware', 'backdoor'],
        'vulnerability': ['vulnerability', 'cve', 'zero-day', 'exploit', 'patch', 'security flaw'],
        'apt': ['apt', 'advanced persistent threat', 'nation-state', 'state-sponsored'],
        'india': ['india', 'indian', 'delhi', 'mumbai', 'bangalore', 'cert-in', 'bengaluru', 'chennai', 'hyderabad'],
    }
