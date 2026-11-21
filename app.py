from flask import Flask, render_template, jsonify, request
from database import Database
from scraper import ThreatScraper
from config import Config
import os
import logging
import httpx
import asyncio

app = Flask(__name__)
app.config.from_object(Config)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
scraper = ThreatScraper()


def _save_threats(threats):
    """Save scraped threats, skipping ones already in the DB.

    Returns a tuple: (added_count, skipped_count).
    Relies on Database.threat_exists() and INSERT IGNORE in add_threat().
    """
    added = 0
    skipped = 0
    for threat in threats:
        url = threat.get('url')
        if url and db.threat_exists(url):
            skipped += 1
            continue
        new_id = db.add_threat(threat)
        if new_id:
            added += 1
        else:
            # add_threat returned None -> INSERT IGNORE skipped a duplicate
            skipped += 1
    return added, skipped


@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/threats')
def get_threats():
    """API endpoint to get threats"""
    category = request.args.get('category')
    severity = request.args.get('severity')
    india_only = request.args.get('india_only') == 'true'
    today_only = request.args.get('today_only') == 'true'
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    threats = db.get_threats(
        limit=limit,
        offset=offset,
        category=category,
        severity=severity,
        india_only=india_only,
        today_only=today_only
    )

    return jsonify(threats)

@app.route('/api/search')
def search_threats():
    """API endpoint to search threats"""
    query = request.args.get('q', '')

    if not query:
        return jsonify([])

    results = db.search_threats(query)
    return jsonify(results)

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """Manually trigger scraping (de-duplicates by URL)."""
    try:
        threats = scraper.scrape_all_sources()
        added_count, skipped_count = _save_threats(threats)

        return jsonify({
            'success': True,
            'message': f'Scraped {len(threats)} articles. Added {added_count}, skipped {skipped_count} duplicates.',
            'added': added_count,
            'skipped': skipped_count,
            'total_scraped': len(threats)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get threat statistics"""
    stats = db.get_stats()
    return jsonify(stats)

@app.route('/api/chat', methods=['POST'])
def chat_with_threat():
    """Chat with AI using CodeWords Gemini - NO RATE LIMITS!"""
    data = request.get_json(silent=True) or {}
    threat_id = data.get('threat_id')
    question = (data.get('question') or '').strip()

    if not question:
        return jsonify({'answer': 'Please enter a question.'}), 400
    if not app.config.get('CODEWORDS_API_KEY'):
        return jsonify({'answer': 'AI chat is not configured yet. Add your own CODEWORDS_API_KEY environment variable to enable it. The dashboard, feed, filters and search work without an AI key.'}), 503

    try:
        # Get the threat from database
        threats = db.get_threats(limit=1000)
        threat = next((t for t in threats if str(t['id']) == str(threat_id)), None)

        if not threat:
            return jsonify({'answer': 'Threat not found'}), 404

        # Create context from threat data
        context = f"""
Threat Information:
Title: {threat['title']}
Description: {threat['description']}
Source: {threat['source']}
Category: {threat['category']}
Severity: {threat['severity']}
Keywords: {', '.join(threat.get('keywords', []))}
India-related: {'Yes' if threat.get('india_related') else 'No'}

Full Content:
{threat.get('raw_content', 'No additional content available')}
"""

        # Call CodeWords Gemini - NO RATE LIMITS!
        answer = asyncio.run(call_codewords_gemini(context, question))

        return jsonify({'answer': answer})

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in AI chat: {error_msg}")

        return jsonify({
            'answer': f' Error: {error_msg}\n\nTroubleshooting:\n1. Check internet connection\n2. Verify API key in config.py\n3. Try again in a moment'
        }), 500

async def call_codewords_gemini(context: str, question: str) -> str:
    """Call CodeWords Gemini API - NO RATE LIMITS!"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                'https://runtime.codewords.ai/run/gemini/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {app.config["CODEWORDS_API_KEY"]}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gemini-2.0-flash-exp',
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a cybersecurity expert assistant. Answer questions about cyber threats clearly and concisely. Focus on practical implications and recommendations for Indian organizations and individuals.'
                        },
                        {
                            'role': 'user',
                            'content': f'Context:\n{context}\n\nQuestion: {question}'
                        }
                    ],
                    'max_tokens': 500,
                    'temperature': 0.7
                }
            )

            response.raise_for_status()
            result = response.json()

            return result['choices'][0]['message']['content']

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"CodeWords API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Gemini call error: {e}")
        raise

if __name__ == '__main__':
    print('Starting Cyber Threat Intelligence Platform...')
    print('Dashboard: http://127.0.0.1:5000')
    print('Database: SQLite (local file)')
    print('AI chat:', 'enabled' if app.config.get('CODEWORDS_API_KEY') else 'not configured (optional)')

    if app.config.get('AUTO_SCRAPE_ON_STARTUP'):
        try:
            scraped = scraper.scrape_all_sources()
            added, skipped = _save_threats(scraped)
            print(f'Scraped {len(scraped)} articles; added {added}, skipped {skipped}.')
        except Exception as exc:
            logger.exception('Startup scraping failed: %s', exc)

    app.run(debug=True, host='127.0.0.1', port=5000)
