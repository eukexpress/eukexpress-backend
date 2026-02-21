# Tracking number generation service

import secrets
import string

TRACKING_PREFIX = 'EUK'
ALLOWED_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

def generate_tracking_number():
    '''Generate random 8-character tracking number in format EUKXXXXX'''
    suffix = ''.join(secrets.choice(ALLOWED_CHARS) for _ in range(5))
    return f'{TRACKING_PREFIX}{suffix}'

def validate_tracking_format(tracking):
    '''Validate tracking number format'''
    import re
    pattern = r'^EUK[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{5}$'
    return bool(re.match(pattern, tracking))