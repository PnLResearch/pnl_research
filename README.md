<div align="center">

# PnL Research

**On-Chain Trading Performance Analytics Engine**

[![Solana](https://img.shields.io/badge/Blockchain-Solana-9945FF?style=flat-square&logo=solana&logoColor=white)](https://solana.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[Website](http://pnlresearch.com) • [Twitter](https://x.com/PnL_Research) • [Features](#-features) • [Getting Started](#-getting-started)

---

*Crypto analytics and visualization platform providing tools for tracking verifiable real-time trading performance with professional, detailed trading records.*

</div>

## 🚀 Overview

**PnL Research** is an advanced analytics and visualization platform built for the cryptocurrency market. We provide precise, verifiable real-time trading performance tracking tools that enable users to deeply analyze professional on-chain trading records and make smarter investment decisions.

We go beyond simple portfolio overviews — our mission is to reveal the real data and strategies behind trading behavior.

## ✨ Features

### Token Data Extraction & Analysis
- Deep analysis of on-chain liquidity, trading volume, and holder distribution
- Track whale movements and identify market sentiment shifts
- Real-time price feeds with historical OHLCV data
- Multi-source data aggregation (Birdeye, Solscan, Helius)

### Wallet Address Intelligence
- Complete historical transaction analysis for any Solana wallet
- Asset composition and PnL performance breakdown
- Identify smart money, institutional, and whale addresses
- Learn from successful trading strategies

### Professional Trading Records
- Transform complex on-chain transactions into clear visualizations
- Reveal trading patterns, entry/exit points, and profit details
- Multi-dimensional data filtering and aggregation
- Custom analysis perspectives and timeframes

## 💡 Why PnL Research?

In a market flooded with noise and misinformation, PnL Research delivers:

| Feature | Description |
|---------|-------------|
| **Transparent & Verifiable** | All data sourced directly from blockchain — trustless and accurate |
| **Real-Time Updates** | Stay ahead with live market dynamics and trading activity |
| **Deep Insights** | Extract actionable intelligence from massive on-chain data |
| **Battle-Tested Infrastructure** | High-performance data pipeline ensuring efficiency and precision |

## 🛠 Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                             │
│  Birdeye API  │  Solscan Pro API  │  Helius RPC            │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Processing Engine                         │
│  • Real-time data ingestion                                │
│  • OHLCV aggregation & normalization                       │
│  • Transaction parsing & classification                    │
│  • Smart caching layer                                     │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              Analytics & Visualization                      │
│  • PnL calculation engine                                  │
│  • K-line chart rendering                                  │
│  • Trade marker overlays                                   │
│  • Performance metrics dashboard                           │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Getting Started

### Prerequisites

- Python 3.11+
- API keys from data providers

### Installation

```bash
# Clone the repository
git clone https://github.com/PnLResearch/pnl_research.git
cd pnl_research

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create a `.env` file:

```env
BIRDEYE_API_KEY=your_birdeye_api_key
SOLSCAN_API_KEY=your_solscan_api_key
HELIUS_API_KEY=your_helius_api_key
```

### Run

```bash
python src/main.py
```

## 🔌 API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/kline/{token}` | GET | OHLCV candlestick data |
| `/api/trades/{wallet}` | GET | Wallet trade history |
| `/api/sync` | POST | Sync on-chain data |
| `/api/health` | GET | Service status |

### Example Request

```bash
curl "http://localhost:8080/api/kline/TOKEN_ADDRESS?interval=1h&limit=168"
```

### Response Format

```json
{
  "success": true,
  "data": [
    {
      "timestamp": 1705900800000,
      "open": 1.2345,
      "high": 1.2500,
      "low": 1.2200,
      "close": 1.2400,
      "volume": 50000
    }
  ]
}
```

## 📊 Supported Data

| Data Type | Source | Update Frequency |
|-----------|--------|------------------|
| Token Prices | Birdeye | Real-time |
| OHLCV Data | Birdeye | 1m / 5m / 15m / 1H / 4H / 1D |
| Transactions | Solscan Pro | Real-time |
| Wallet History | Helius | On-demand |

## 🗺 Roadmap

- [x] Multi-source data aggregation
- [x] OHLCV processing engine
- [x] Wallet PnL calculation
- [ ] WebSocket real-time feeds
- [ ] Advanced portfolio analytics
- [ ] Mobile app integration
- [ ] Public API access

## 🌐 Connect With Us

<div align="center">

[![Website](https://img.shields.io/badge/Website-pnlresearch.com-blue?style=for-the-badge)](http://pnlresearch.com)
[![Twitter](https://img.shields.io/badge/Twitter-@PnL__Research-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://x.com/PnL_Research)

</div>

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built for traders, by traders.**

[Website](http://pnlresearch.com) • [Twitter](https://x.com/PnL_Research)

</div>
