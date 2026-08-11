import os
import sys
import time

# Add app to path
sys.path.insert(0, os.path.abspath('.'))

from dotenv import load_dotenv
load_dotenv()

print('API KEY:', bool(os.getenv('GEMINI_API_KEY')))

start = time.time()
try:
    from app.services.ai_service import analyze_chat
    res = analyze_chat('안녕')
    print('Result:', res)
except Exception as e:
    print('Error:', e)
print('Took:', time.time() - start, 'seconds')
