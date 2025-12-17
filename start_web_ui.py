#!/usr/bin/env python3
"""
Start the Trust & Safety Newsletter Web UI
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
except ImportError:
    # dotenv not available, environment variables must be set manually
    pass

# Add ts_newsletter to path
sys.path.insert(0, str(Path(__file__).parent))

# Set default output directory if not set
if 'TS_NEWSLETTER_OUTPUT_DIR' not in os.environ:
    os.environ['TS_NEWSLETTER_OUTPUT_DIR'] = str(Path(__file__).parent / 'output' / 'newsletters')

# Import and run Flask app
from ts_newsletter.web_ui.app import main

if __name__ == '__main__':
    main()
