# src/utils/rate_limiter.py
import requests
import time
from utils.log import log_message

# GITHUB_TOKEN = 'your_github_token_here'

BASE_URL = 'https://api.github.com'

def check_rate_limit(headers, log_file):
    
    rate_limit_url = f'{BASE_URL}/rate_limit'
    response = requests.get(rate_limit_url, headers=headers)
    rate_limit_data = response.json()
    remaining = rate_limit_data['rate']['remaining']
    reset_time = rate_limit_data['rate']['reset']
    # log_message(f'Rate limit: {remaining} remaining, resets at {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reset_time))}', log_file)
    return remaining, reset_time
