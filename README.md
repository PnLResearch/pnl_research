<div align="center">

# PnL Research

**On-Chain Trading Performance Analytics Platform**

[![Solana](https://img.shields.io/badge/Blockchain-Solana-9945FF?style=flat-square&logo=solana&logoColor=white)](https://solana.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[Website](http://pnlresearch.com) • [Twitter](https://x.com/PnL_Research) • [Contact](mailto:team@pnlresearch.com)

---

*Crypto analytics and visualization platform providing tools for tracking verifiable real-time trading performance with professional, detailed trading records.*

</div>

## Overview

**PnL Research** is an advanced analytics platform built for the cryptocurrency market. We provide precise, verifiable real-time trading performance tracking tools that enable users to deeply analyze professional on-chain trading records.

Our mission is to reveal the real data and strategies behind trading behavior through transparent, blockchain-sourced analytics.

## Core Features

### Token Data Extraction
- Real-time token price feeds from multiple data sources
- Historical OHLCV data with configurable intervals
- On-chain liquidity and trading volume analysis
- Holder distribution and whale tracking

### Wallet Address Intelligence
- Complete transaction history analysis for any Solana wallet
- Asset composition breakdown and portfolio tracking
- PnL calculation with entry/exit point identification
- Smart money and institutional address detection

### Trading Records Analysis
- Detailed swap and trade record parsing
- Multi-dimensional filtering and data aggregation
- Performance metrics calculation (win rate, ROI, drawdown)
- Export capabilities for further analysis

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                             │
│         Birdeye  │  Solscan Pro  │  Helius RPC             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Processing Layer                      │
│  • Multi-source aggregation    • OHLCV normalization       │
│  • Transaction classification  • Caching & persistence     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Analytics Engine                          │
│  • PnL computation            • Performance metrics        │
│  • Pattern recognition        • Risk analysis              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Visualization Layer                       │
│  • Interactive dashboards     • Real-time charts           │
│  • Trade timeline views       • Export & reporting         │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11+, Flask, AsyncIO |
| **Data Sources** | Birdeye API, Solscan Pro API, Helius RPC |
| **Database** | PostgreSQL, Redis (caching) |
| **Frontend** | JavaScript, React |
| **Infrastructure** | Docker, AWS |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/token/{address}` | GET | Token data and metrics |
| `/api/wallet/{address}` | GET | Wallet analysis and PnL |
| `/api/trades/{wallet}` | GET | Trade history records |
| `/api/kline/{token}` | GET | OHLCV candlestick data |

## Project Structure

```
pnl_research/
├── src/
│   ├── api/                    # API client implementations
│   ├── data_processing/        # Data aggregation & normalization
│   └── main.py                 # Application entry point
├── frontend/                   # Web interface
├── config/                     # Configuration management
├── data/                       # Data storage
└── tests/                      # Test suite
```

## Branches

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code |
| `database` | Database schema and migrations |
| `data-analysis` | Analytics engine development |
| `data-visualization` | Charts and visualization components |
| `frontend` | User interface development |
| `user-interaction` | User features and authentication |

## Roadmap

- [x] Multi-source data aggregation
- [x] OHLCV processing engine
- [x] Wallet PnL calculation
- [ ] Real-time WebSocket feeds
- [ ] Advanced portfolio analytics
- [ ] Public API access
- [ ] Mobile application

## Contact

<div align="center">

[![Website](https://img.shields.io/badge/Website-pnlresearch.com-blue?style=for-the-badge)](http://pnlresearch.com)
[![Twitter](https://img.shields.io/badge/Twitter-@PnL__Research-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://x.com/PnL_Research)
[![Email](https://img.shields.io/badge/Email-team@pnlresearch.com-red?style=for-the-badge&logo=gmail&logoColor=white)](mailto:team@pnlresearch.com)

</div>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built for traders, by traders.**

</div>
