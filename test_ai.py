import os
import sys
import time

# Add app to path
sys.path.insert(0, os.path.abspath('.'))

from dotenv import load_dotenv
load_dotenv()

print('OPENAI API KEY:', bool(os.getenv('OPENAI_API_KEY')))
print('MODEL:', os.getenv('OPENAI_MODEL', 'gpt-5.6-luna'))

start = time.time()
try:
    from app.services.ai_service import analyze_chat
    res = analyze_chat('안녕')
    print('Result:', res)
except Exception as e:
    print('Error:', e)
print('Took:', time.time() - start, 'seconds')
