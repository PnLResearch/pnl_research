"""
PnL Research - Main Entry Point

This is the main server that:
1. Fetches on-chain data from Birdeye, Solscan, Helius
2. Processes and aggregates data into OHLCV format
3. Serves K-line chart visualization via web interface
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from config.settings import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG,
    BIRDEYE_API_KEY, validate_config, FRONTEND_DIR
)

app = Flask(__name__, static_folder=os.path.join(FRONTEND_DIR, 'static'))
CORS(app)


# ============================================================================
# API Routes
# ============================================================================

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'PnL Research API',
        'version': '1.0.0'
    })


@app.route('/api/kline/<token>')
def get_kline(token):
    """
    Get OHLCV K-line data for a token

    Query params:
        - interval: 1m, 5m, 15m, 1h, 4h, 1d (default: 1m)
        - limit: number of candles (default: 1000)
        - from: start timestamp (optional)
        - to: end timestamp (optional)
    """
    interval = request.args.get('interval', '1m')
    limit = int(request.args.get('limit', 1000))

    # TODO: Implement actual data fetching from Birdeye
    # This is a placeholder response
    return jsonify({
        'success': True,
        'token': token,
        'interval': interval,
        'data': [],
        'message': 'K-line endpoint ready. Implement data fetching.'
    })


@app.route('/api/trades/<wallet>')
def get_trades(wallet):
    """
    Get trade history for a wallet

    Query params:
        - token: filter by token address (optional)
        - limit: number of trades (default: 100)
    """
    token = request.args.get('token')
    limit = int(request.args.get('limit', 100))

    # TODO: Implement actual trade fetching from Solscan/Helius
    return jsonify({
        'success': True,
        'wallet': wallet,
        'token': token,
        'data': [],
        'message': 'Trades endpoint ready. Implement data fetching.'
    })


@app.route('/api/sync', methods=['POST'])
def sync_data():
    """
    Trigger data sync from on-chain sources

    Body:
        - token: token address to sync
        - interval: data interval (default: 1m)
        - hours: hours of history to sync (default: 24)
    """
    data = request.get_json() or {}
    token = data.get('token')
    interval = data.get('interval', '1m')
    hours = data.get('hours', 24)

    if not token:
        return jsonify({'success': False, 'error': 'Token address required'}), 400

    # TODO: Implement actual sync logic
    return jsonify({
        'success': True,
        'token': token,
        'interval': interval,
        'hours': hours,
        'message': 'Sync endpoint ready. Implement sync logic.'
    })


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("PnL Research - On-Chain Data Analysis Tool")
    print("=" * 60)

    # Validate configuration
    if not validate_config():
        print("\n[WARNING] Some API keys are missing. Check your .env file.")
        print("The server will start, but some features may not work.\n")

    print(f"\nStarting server at http://{FLASK_HOST}:{FLASK_PORT}")
    print("Press Ctrl+C to stop.\n")

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
