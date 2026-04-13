"""
Daily News Bot - GitHub Actions లో రోజూ 8AM IST కి auto run అవుతుంది
17 RSS feeds నుండి 51 news fetch చేసి, AI తో summarize చేసి, Google Drive లో save చేస్తుంది
"""

import feedparser
import os
import json
from datetime import datetime
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
NEWS_PER_FEED = 3
DRIVE_FOLDER_NAME = "Daily News"

RSS_FEEDS = [
    {"name": "Breaking News",  "url": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "World News",     "url": "https://news.google.com/rss/search?q=world&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Politics",       "url": "https://news.google.com/rss/search?q=politics&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Business",       "url": "https://news.google.com/rss/search?q=business&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Technology",     "url": "https://news.google.com/rss/search?q=technology&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Sports",         "url": "https://news.google.com/rss/search?q=sports&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Entertainment",  "url": "https://news.google.com/rss/search?q=entertainment&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Science",        "url": "https://news.google.com/rss/search?q=science&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Environment",    "url": "https://news.google.com/rss/search?q=environment&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Education",      "url": "https://news.google.com/rss/search?q=education&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Health",         "url": "https://news.google.com/rss/search?q=health&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Lifestyle",      "url": "https://news.google.com/rss/search?q=lifestyle&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Movies",         "url": "https://news.google.com/rss/search?q=movies&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Gaming",         "url": "https://news.google.com/rss/search?q=gaming&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Telugu News",    "url": "https://news.google.com/rss?hl=te&gl=IN&ceid=IN:te"},
    {"name": "Best Deals",     "url": "https://news.google.com/rss/search?q=best+deals+OR+discounts+OR+offers+OR+sales&hl=en-IN&gl=IN&ceid=IN:en"},
    {"name": "Motivation",     "url": "https://news.google.com/rss/search?q=motivation+OR+inspirational+stories&hl=en-IN&gl=IN&ceid=IN:en"},
]

def summarize_news(title, description):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"Summarize in 2 sentences:\nTitle: {title}\nContent: {description[:400]}")
        return response.text.strip()
    except Exception as e:
        return f"(Summary unavailable)"

def fetch_all_news():
    all_news = []
    for feed_info in RSS_FEEDS:
        print(f"📡 {feed_info['name']}...")
        try:
            feed = feedparser.parse(feed_info['url'])
            for entry in feed.entries[:NEWS_PER_FEED]:
                title = entry.get('title', 'No Title')
                description = entry.get('summary', '')
                summary = summarize_news(title, description)
                all_news.append({
                    'category': feed_info['name'],
                    'title': title,
                    'summary': summary,
                    'link': entry.get('link', '')
                })
        except Exception as e:
            print(f"   ❌ Error: {e}")
    return all_news

def format_document(news_list):
    today = datetime.now().strftime("%B %d, %Y")
    content = f"📰 DAILY NEWS DIGEST\nDate: {today}\nTotal: {len(news_list)} articles\n{'='*55}\n"
    current_category = ""
    for news in news_list:
        if news['category'] != current_category:
            current_category = news['category']
            content += f"\n\n{'─'*55}\n📌 {current_category.upper()}\n{'─'*55}\n"
        content += f"\n📰 {news['title']}\n📝 {news['summary']}\n🔗 {news['link']}\n"
    return content

def get_drive_service():
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    token_data = json.loads(os.environ.get("GOOGLE_TOKEN", "{}"))
    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=SCOPES
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)

def save_to_drive(content, filename):
    try:
        service = get_drive_service()
        query = f"name='Daily News' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id)").execute()
        folders = results.get('files', [])
        if folders:
            folder_id = folders[0]['id']
        else:
            folder = service.files().create(
                body={'name': 'Daily News', 'mimeType': 'application/vnd.google-apps.folder'},
                fields='id'
            ).execute()
            folder_id = folder['id']

        media = MediaInMemoryUpload(content.encode('utf-8'), mimetype='text/plain')
        file = service.files().create(
            body={'name': filename, 'parents': [folder_id]},
            media_body=media,
            fields='id,name'
        ).execute()
        print(f"✅ Saved: {filename} (ID: {file['id']})")
    except Exception as e:
        print(f"❌ Drive error: {e}")

def main():
    print(f"🚀 Starting | {datetime.now().strftime('%Y-%m-%d %H:%M')} IST")
    news_list = fetch_all_news()
    print(f"✅ {len(news_list)} articles fetched")
    document = format_document(news_list)
    filename = f"News_{datetime.now().strftime('%Y-%m-%d')}.txt"
    save_to_drive(document, filename)
    print("🎉 Done! Check Google Drive → 'Daily News' folder")

if __name__ == "__main__":
    main()
