"""
PnL Research - Configuration Settings
Centralized management of API keys and global configuration

IMPORTANT: API keys are loaded from environment variables.
Copy .env.example to .env and fill in your keys.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# API Keys (loaded from environment variables)
# ============================================================================

# Birdeye API - Token price and OHLCV data
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")

# Solscan Pro API - Transaction and wallet data
SOLSCAN_PRO_TOKEN = os.getenv("SOLSCAN_API_KEY", "")

# Helius API - Solana RPC and enhanced APIs
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")

# Google Gemini API (optional, for AI features)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


# ============================================================================
# Data Source Assignment
# ============================================================================
# Helius:   Raw transaction data fetching (Enhanced Transactions API)
# Birdeye:  Historical price query (Primary source, /defi/historical_price_unix)
# Solscan:  Historical price query (Backup source)


# ============================================================================
# Path Configuration
# ============================================================================

# Project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# Source code directory
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

# Frontend directory
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")


# ============================================================================
# Server Configuration
# ============================================================================

FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "8080"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"


# ============================================================================
# Constants
# ============================================================================

# SOL Mint address
SOL_MINT = "So11111111111111111111111111111111111111112"

# Default token decimals (Solana standard)
DEFAULT_DECIMALS = 9

# OHLCV intervals supported
SUPPORTED_INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"]


# ============================================================================
# Validation
# ============================================================================

def validate_config():
    """Check if required API keys are configured"""
    missing = []

    if not BIRDEYE_API_KEY:
        missing.append("BIRDEYE_API_KEY")
    if not SOLSCAN_PRO_TOKEN:
        missing.append("SOLSCAN_API_KEY")
    if not HELIUS_API_KEY:
        missing.append("HELIUS_API_KEY")

    if missing:
        print(f"[WARNING] Missing API keys: {', '.join(missing)}")
        print("Please configure them in your .env file")
        return False

    return True
