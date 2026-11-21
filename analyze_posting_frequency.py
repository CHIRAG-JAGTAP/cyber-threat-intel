#!/usr/bin/env python3
"""
Analyze daily article posting frequency for the 4 referenced cybersecurity news sites.
"""
import feedparser
from datetime import datetime, timedelta
import time
from collections import defaultdict

# RSS feed URLs from config
SOURCES = [
    {
        'name': 'The Hacker News',
        'feed_url': 'https://feeds.feedburner.com/TheHackersNews',
        'url': 'https://thehackernews.com/'
    },
    {
        'name': 'Cybersecurity News',
        'feed_url': 'https://cybersecuritynews.com/feed/',
        'url': 'https://cybersecuritynews.com/'
    },
    {
        'name': 'Krebs on Security',
        'feed_url': 'https://krebsonsecurity.com/feed/',
        'url': 'https://krebsonsecurity.com/'
    },
    {
        'name': 'Bleeping Computer',
        'feed_url': 'https://www.bleepingcomputer.com/feed/',
        'url': 'https://www.bleepingcomputer.com/'
    }
]

out_lines = []

def log(msg):
    out_lines.append(msg)
    print(msg)

def parse_date(entry):
    """Extract and parse publish date from RSS entry."""
    date_str = entry.get('published', entry.get('updated', entry.get('pubDate', '')))
    if not date_str:
        return None
    
    if 'published_parsed' in entry and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    elif 'updated_parsed' in entry and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    
    for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ', '%a, %d %b %Y %H:%M:%S GMT']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def analyze_source(source):
    log("")
    log("="*60)
    log("Analyzing: " + source['name'])
    log("="*60)
    
    try:
        feed = feedparser.parse(source['feed_url'])
        entries = feed.entries
        
        if not entries:
            log("  [X] No entries found in RSS feed")
            return None
        
        log("  [OK] Fetched " + str(len(entries)) + " articles from RSS feed")
        
        dates = []
        date_counts = defaultdict(int)
        
        for entry in entries:
            dt = parse_date(entry)
            if dt:
                dates.append(dt)
                date_key = dt.strftime('%Y-%m-%d')
                date_counts[date_key] += 1
        
        if not dates:
            log("  [X] Could not parse dates from articles")
            return None
        
        dates.sort()
        newest = max(dates)
        oldest = min(dates)
        date_range = (newest - oldest).days
        
        log("")
        log("  ARTICLE STATISTICS:")
        log("     Newest article: " + newest.strftime('%Y-%m-%d %H:%M'))
        log("     Oldest article: " + oldest.strftime('%Y-%m-%d %H:%M'))
        log("     Date span: " + str(date_range) + " days")
        
        now = datetime.now()
        last_24h = [d for d in dates if (now - d).total_seconds() <= 86400]
        last_7d = [d for d in dates if (now - d).days <= 7]
        
        log("")
        log("  LAST 24 HOURS: " + str(len(last_24h)) + " articles")
        log("  LAST 7 DAYS: " + str(len(last_7d)) + " articles")
        
        if date_range > 0:
            daily_avg = len(dates) / date_range
        else:
            daily_avg = len(dates)
        
        log("")
        log("  DAILY AVERAGE:")
        log("     Total articles in feed: " + str(len(dates)))
        log("     Average articles/day: " + str(round(daily_avg, 2)))
        
        log("")
        log("  DAILY BREAKDOWN:")
        sorted_dates = sorted(date_counts.keys())
        for date_key in sorted_dates[-7:]:
            bar = '#' * min(date_counts[date_key], 20)
            log("     " + date_key + ": " + str(date_counts[date_key]) + " articles " + bar)
        
        if daily_avg < 1:
            if daily_avg > 0:
                estimate = "~1 article every " + str(int(1/daily_avg)) + " days"
            else:
                estimate = "unknown"
        else:
            estimate = "~" + str(int(daily_avg)) + " articles/day"
        
        log("")
        log("  ESTIMATED FREQUENCY: " + estimate)
        
        return {
            'name': source['name'],
            'total_fetched': len(entries),
            'parsed_with_dates': len(dates),
            'daily_average': daily_avg,
            'last_24h': len(last_24h),
            'last_7d': len(last_7d),
            'date_span_days': date_range,
            'date_counts': dict(date_counts)
        }
        
    except Exception as e:
        log("  [X] Error: " + str(e))
        return None

def main():
    log("")
    log("="*60)
    log("CYBER THREAT INTELLIGENCE - SOURCE ANALYSIS")
    log("Analyzing daily article posting frequency...")
    log("="*60)
    
    results = []
    for source in SOURCES:
        result = analyze_source(source)
        if result:
            results.append(result)
        time.sleep(1)
    
    # Summary
    log("")
    log("="*60)
    log("SUMMARY COMPARISON TABLE")
    log("="*60)
    log(f"{'Source':<25} {'Daily Avg':>10} {'Last 24h':>10} {'Last 7d':>10} {'Feed Size':>10}")
    log("-" * 65)
    
    for r in results:
        log(f"{r['name']:<25} {r['daily_average']:>10.2f} {r['last_24h']:>10} {r['last_7d']:>10} {r['total_fetched']:>10}")
    
    total_daily = sum(r['daily_average'] for r in results)
    log("-" * 65)
    log(f"{'TOTAL ESTIMATED':<25} {total_daily:>10.2f}")
    
    log("")
    log("="*60)
    log("RECOMMENDATIONS:")
    log("="*60)
    
    results_sorted = sorted(results, key=lambda x: x['daily_average'], reverse=True)
    log("")
    log("  By posting frequency (most to least active):")
    for i, r in enumerate(results_sorted, 1):
        log("  " + str(i) + ". " + r['name'] + ": ~" + str(round(r['daily_average'], 1)) + " articles/day")
    
    if total_daily > 0:
        interval_minutes = int(1440 / total_daily * 0.5)
        interval_minutes = max(15, min(60, interval_minutes))
        log("")
        log("  Recommended scraping interval: Every " + str(interval_minutes) + " minutes")
        log("     (to catch ~95% of new articles within 30 minutes of publishing)")
    
    log("")
    log("  Estimated database growth:")
    log("     - Per day: ~" + str(round(total_daily)) + " articles")
    log("     - Per month: ~" + str(round(total_daily * 30)) + " articles")
    log("     - Per year: ~" + str(round(total_daily * 365)) + " articles")
    log("     (at current rates, without duplicates)")
    
    # Write to output file
    with open('analysis_output.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))
    log("")
    log("[Output also saved to analysis_output.txt]")

if __name__ == '__main__':
    main()
