"""Schedule with Windows Task Scheduler or cron, e.g. at 06:10 KST each day.
This fetches HEADLINES and official links only; never republishes article bodies.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import refresh_news
if __name__=='__main__':
    print('RSS processed:',refresh_news())
