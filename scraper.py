import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
from config import Config
import re
import logging

logger = logging.getLogger(__name__)

class ThreatScraper:
    def __init__(self):
        self.config = Config()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_all_sources(self):
        """Scrape all configured news sources"""
        all_threats = []
        
        for source in self.config.NEWS_SOURCES:
            try:
                logger.info(f"Scraping {source['name']}...")
                
                if source['type'] == 'rss':
                    threats = self.scrape_rss_feed(source)
                else:
                    # Use CodeWords Firecrawl if enabled, otherwise BeautifulSoup
                    if self.config.USE_CODEWORDS_SCRAPING:
                        threats = self.scrape_with_firecrawl(source)
                    else:
                        threats = self.scrape_website(source)
                
                all_threats.extend(threats)
                logger.info(f" Scraped {len(threats)} threats from {source['name']}")
                
            except Exception as e:
                logger.error(f" Error scraping {source['name']}: {e}")
        
        return all_threats
    
    def scrape_with_firecrawl(self, source):
        """Scrape using CodeWords Firecrawl (no API key needed)"""
        threats = []
        
        try:
            from firecrawl import FirecrawlApp
            
            client = FirecrawlApp()
            
            scraped_data = client.scrape_url(
                source['url'],
                params={
                    "formats": ["markdown"],
                    "timeout": 10000,
                    "waitFor": 1000
                }
            )
            
            # Extract markdown content
            markdown = scraped_data.markdown if hasattr(scraped_data, 'markdown') else scraped_data.get('markdown', '')
            
            if markdown:
                # Parse markdown for threat information
                lines = markdown.split('\n')
                current_threat = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for headlines (potential threats)
                    if line.startswith('#') and len(line) > 10:
                        if current_threat:
                            analyzed = self.analyze_threat(current_threat)
                            threats.append(analyzed)
                        
                        current_threat = {
                            'title': line.replace('#', '').strip(),
                            'description': '',
                            'url': source['url'],
                            'source': source['name'],
                            'published_date': datetime.now().isoformat(),
                            'raw_content': ''
                        }
                    elif current_threat and line:
                        current_threat['description'] += line + ' '
                        current_threat['raw_content'] += line + '\n'
                
                # Add last threat
                if current_threat:
                    analyzed = self.analyze_threat(current_threat)
                    threats.append(analyzed)
        
        except Exception as e:
            logger.error(f"Firecrawl error for {source['url']}: {e}")
        
        return threats[:5]  # Limit to 5 most recent
    
    def _parse_rss_date(self, entry):
        """Extract original published date from RSS entry as ISO string."""
        # feedparser provides published_parsed as a time tuple (UTC)
        parsed = entry.get('published_parsed') or entry.get('updated_parsed')
        if parsed:
            try:
                dt = datetime(*parsed[:6])
                return dt.isoformat()
            except Exception:
                pass
        # Fallback: try raw published string
        raw = entry.get('published') or entry.get('updated')
        if raw:
            for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z',
                        '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ']:
                try:
                    return datetime.strptime(raw, fmt).isoformat()
                except ValueError:
                    continue
        return datetime.now().isoformat()

    def scrape_rss_feed(self, source):
        """Scrape RSS feed"""
        threats = []
        feed = feedparser.parse(source['feed_url'])
        
        for entry in feed.entries[:10]:  # Limit to 10 most recent
            threat = {
                'title': entry.title,
                'description': entry.get('summary', ''),
                'url': entry.link,
                'source': source['name'],
                'published_date': self._parse_rss_date(entry),
                'raw_content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else entry.get('summary', '')
            }
            
            # Analyze threat
            analyzed = self.analyze_threat(threat)
            threats.append(analyzed)
        
        return threats
    
    def scrape_website(self, source):
        """Scrape website content using BeautifulSoup"""
        threats = []
        
        try:
            response = requests.get(source['url'], headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Generic scraping - look for article headlines
            articles = soup.find_all(['article', 'div'], class_=re.compile('(post|article|entry|item)', re.I))
            
            if not articles:
                # Fallback: find all h2, h3 tags
                articles = soup.find_all(['h2', 'h3'])
            
            for article in articles[:5]:
                title_elem = article.find(['h1', 'h2', 'h3', 'a'])
                if title_elem:
                    threat = {
                        'title': title_elem.get_text(strip=True),
                        'description': article.get_text(strip=True)[:500],
                        'url': source['url'],
                        'source': source['name'],
                        'published_date': datetime.now().isoformat(),
                        'raw_content': article.get_text(strip=True)
                    }
                    analyzed = self.analyze_threat(threat)
                    threats.append(analyzed)
        
        except Exception as e:
            logger.error(f"Error scraping {source['url']}: {e}")
        
        return threats
    
    def analyze_threat(self, threat):
        """Analyze threat content for categorization"""
        content = (threat['title'] + ' ' + threat['description'] + ' ' + threat.get('raw_content', '')).lower()
        
        # Detect category
        detected_keywords = []
        category = 'other'
        
        for cat, keywords in self.config.THREAT_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in content:
                    detected_keywords.append(keyword)
                    if category == 'other':
                        category = cat
        
        # Check if India-related
        india_related = any(kw in content for kw in self.config.THREAT_KEYWORDS['india'])
        
        # Calculate severity
        severity = self.calculate_severity(content, detected_keywords)
        
        threat['category'] = category
        threat['severity'] = severity
        threat['keywords'] = list(set(detected_keywords))[:10]  # Unique, max 10
        threat['india_related'] = india_related
        
        return threat
    
    def calculate_severity(self, content, keywords):
        """Calculate threat severity based on keywords and content"""
        severity_score = 0
        
        # Critical keywords
        critical_words = ['zero-day', 'critical', 'actively exploited', 'ransomware', 'nation-state', 'emergency', 'urgent']
        high_words = ['vulnerability', 'breach', 'attack', 'compromise', 'hack', 'exploit']
        medium_words = ['phishing', 'malware', 'suspicious', 'warning', 'alert']
        
        for word in critical_words:
            if word in content:
                severity_score += 10
        
        for word in high_words:
            if word in content:
                severity_score += 7
        
        for word in medium_words:
            if word in content:
                severity_score += 5
        
        # Map score to severity
        if severity_score >= 10:
            return 'critical'
        elif severity_score >= 7:
            return 'high'
        elif severity_score >= 5:
            return 'medium'
        elif severity_score >= 3:
            return 'low'
        else:
            return 'info'