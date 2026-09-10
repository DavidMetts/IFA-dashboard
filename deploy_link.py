"""Print a deployment setup URL for an actual GitHub repository."""
import re
import sys
from urllib.parse import urlencode

if __name__ == '__main__':
    if len(sys.argv)!=2 or not re.fullmatch(r'[\w.-]+/[\w.-]+',sys.argv[1]):
        raise SystemExit('Usage: python deploy_link.py OWNER/REPO')
    print('https://share.streamlit.io/deploy?'+urlencode(dict(repository=sys.argv[1],branch='main',mainModule='app.py')))
