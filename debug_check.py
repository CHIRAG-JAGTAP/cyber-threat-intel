import sys
import os

print(f"Python version: {sys.version}")

try:
    import flask
    print("Flask imported")
except ImportError as e:
    print(f"Flask import failed: {e}")

try:
    import mysql.connector
    print("mysql.connector imported")
except ImportError as e:
    print(f"mysql.connector import failed: {e}")

try:
    import feedparser
    print("feedparser imported")
except ImportError as e:
    print(f"feedparser import failed: {e}")

try:
    import firecrawl
    print("firecrawl imported")
except ImportError as e:
    print(f"firecrawl import failed: {e}")

try:
    from config import Config
    print("Config imported")
    print(f"DB Config: Host={Config.MYSQL_HOST}, User={Config.MYSQL_USER}")
except Exception as e:
    print(f"Config import failed: {e}")

try:
    from database import Database
    print("Database module imported")
    # Don't instantiate yet, just check import
except Exception as e:
    print(f"Database import failed: {e}")

try:
    from scraper import ThreatScraper
    print("Scraper module imported")
except Exception as e:
    print(f"Scraper import failed: {e}")
