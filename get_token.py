"""
get_token.py - ఒకసారి మాత్రమే run చేయాలి
Google Drive permission తీసుకుంటుంది, token.json save చేస్తుంది
"""
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']

print("🔐 Google Drive Permission తీసుకుంటున్నాం...")
print("Browser లో Google account select చేసి Allow click చేయండి\n")

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

token_data = {
    'token': creds.token,
    'refresh_token': creds.refresh_token,
    'token_uri': creds.token_uri,
    'client_id': creds.client_id,
    'client_secret': creds.client_secret,
}

with open('token.json', 'w') as f:
    json.dump(token_data, f, indent=2)

print("✅ token.json తయారైంది!")
print("\n📋 ఇప్పుడు token.json contents copy చేసి")
print("   GitHub Secret లో GOOGLE_TOKEN గా paste చేయండి")
print("\ntoken.json contents:")
print("─" * 40)
with open('token.json') as f:
    print(f.read())
