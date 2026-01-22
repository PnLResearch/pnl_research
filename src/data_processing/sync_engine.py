"""
PnLResearch V2.0 - Atomic Data Synchronization Engine

Provides atomic file operations and data normalization for safe concurrent access.
Uses os.replace() for atomic writes to prevent corruption during UI reads.

Key Features:
- atomic_save(): Write-then-replace for safe file updates
- atomic_load(): Safe JSON loading with error handling
- normalize_price(): Divide raw price by 10^decimals
- KLineNormalizer: Batch normalize OHLCV data from Birdeye
"""

import os
import sys
import json
import time
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
from init_dirs import CHART_LIBRARY_DIR, get_kline_path


# =============================================================================
# Atomic File Operations
# =============================================================================

def atomic_save(path: Union[str, Path], data: Any, indent: int = 2) -> bool:
    """
    Atomically save data to JSON file using write-then-replace pattern.

    This prevents file corruption if the UI reads during a write operation.
    Data is written to a temp file, then atomically moved to the target path.

    Args:
        path: Target file path
        data: JSON-serializable data
        indent: JSON indentation (default: 2)

    Returns:
        True if successful, False on error

    Example:
        >>> atomic_save("/data/klines.json", [[1234567890, 1.0, 1.1, 0.9, 1.05, 1000]])
    """
    path = Path(path)

    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file in same directory (same filesystem for atomic rename)
        fd, temp_path = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.stem}_",
            suffix=".tmp"
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)

            # Atomic replace (POSIX guarantees atomicity for os.replace)
            os.replace(temp_path, path)
            return True

        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    except Exception as e:
        print(f"[atomic_save] Error saving {path}: {e}")
        return False


def atomic_load(path: Union[str, Path], default: Any = None) -> Any:
    """
    Safely load JSON data from file.

    Args:
        path: File path to load
        default: Value to return if file doesn't exist or is invalid

    Returns:
        Parsed JSON data or default value
    """
    path = Path(path)

    if not path.exists():
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[atomic_load] Error loading {path}: {e}")
        return default


# =============================================================================
# Price Normalization
# =============================================================================

def normalize_price(raw_price: Union[int, float], decimals: int = 9) -> float:
    """
    Normalize raw price by dividing by 10^decimals.

    Birdeye V3 API returns raw amounts that need normalization.

    Args:
        raw_price: Raw price value from API
        decimals: Token decimals (default: 9 for SOL)

    Returns:
        Normalized price as float

    Example:
        >>> normalize_price(1000000000, 9)  # 1 SOL
        1.0
        >>> normalize_price(1000000, 6)     # 1 USDC
        1.0
    """
    if raw_price is None or raw_price == 0:
        return 0.0
    return float(raw_price) / (10 ** decimals)


def normalize_amount(raw_amount: Union[int, float], decimals: int) -> float:
    """
    Normalize raw token amount by dividing by 10^decimals.

    Args:
        raw_amount: Raw amount from API
        decimals: Token decimals

    Returns:
        Normalized amount as float
    """
    return normalize_price(raw_amount, decimals)


# =============================================================================
# K-Line Data Structures
# =============================================================================

@dataclass
class KLineBar:
    """Single K-line bar with OHLCV data."""
    timestamp: int      # Unix timestamp (seconds)
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_list(self) -> List:
        """Convert to list format for KLineChart."""
        return [
            self.timestamp * 1000,  # KLineChart expects milliseconds
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume
        ]

    def to_dict(self) -> Dict:
        """Convert to dict format for KLineChart."""
        return {
            "timestamp": self.timestamp * 1000,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }

    @classmethod
    def from_birdeye(cls, item: Dict, decimals: int = 0) -> "KLineBar":
        """
        Create from Birdeye API response item.

        Birdeye format: {o, h, l, c, v, unixTime}

        Args:
            item: Birdeye OHLCV item
            decimals: Token decimals for normalization (0 = already normalized)
        """
        divisor = 10 ** decimals if decimals > 0 else 1

        return cls(
            timestamp=item.get("unixTime", 0),
            open=item.get("o", 0) / divisor,
            high=item.get("h", 0) / divisor,
            low=item.get("l", 0) / divisor,
            close=item.get("c", 0) / divisor,
            volume=item.get("v", 0)
        )


class KLineNormalizer:
    """
    Normalize and cache K-line data from Birdeye.

    Handles:
    - Price normalization (raw / 10^decimals)
    - Format conversion to KLineChart spec
    - Atomic file persistence
    """

    def __init__(self, mint_address: str, decimals: int = 0):
        """
        Args:
            mint_address: Token mint address
            decimals: Token decimals for price normalization (0 = skip)
        """
        self.mint_address = mint_address
        self.decimals = decimals
        self.cache_path = get_kline_path(mint_address)

    def normalize_birdeye_response(self, items: List[Dict]) -> List[Dict]:
        """
        Convert Birdeye OHLCV response to KLineChart format.

        Input (Birdeye): [{o, h, l, c, v, unixTime}, ...]
        Output (KLineChart): [{timestamp, open, high, low, close, volume}, ...]

        Args:
            items: List of Birdeye OHLCV items

        Returns:
            List of K-line bars in dict format
        """
        result = []
        for item in items:
            bar = KLineBar.from_birdeye(item, self.decimals)
            result.append(bar.to_dict())

        # Sort by timestamp ascending
        result.sort(key=lambda x: x["timestamp"])
        return result

    def save(self, klines: List[Dict]) -> bool:
        """
        Atomically save K-line data to cache.

        Args:
            klines: List of K-line bars [{ts, o, h, l, c, v}, ...]

        Returns:
            True if successful
        """
        return atomic_save(self.cache_path, klines)

    def load(self) -> List[Dict]:
        """
        Load K-line data from cache.

        Returns:
            List of K-line bars or empty list
        """
        return atomic_load(self.cache_path, default=[])

    def merge_and_save(self, new_klines: List[Dict]) -> List[Dict]:
        """
        Merge new K-lines with existing cache and save.

        Deduplicates by timestamp and sorts ascending.

        Args:
            new_klines: New K-line data to merge

        Returns:
            Merged K-line data
        """
        existing = self.load()

        # Build timestamp -> kline map (newer data overwrites)
        kline_map = {k["timestamp"]: k for k in existing}
        for k in new_klines:
            kline_map[k["timestamp"]] = k

        # Sort by timestamp
        merged = sorted(kline_map.values(), key=lambda x: x["timestamp"])

        self.save(merged)
        return merged


# =============================================================================
# Trade Data Normalization
# =============================================================================

@dataclass
class TradeRecord:
    """Normalized trade record."""
    timestamp: int          # Unix timestamp (seconds)
    signature: str          # Transaction signature
    side: str               # 'buy' or 'sell'
    token_mint: str         # Token being traded
    token_amount: float     # Normalized token amount
    sol_amount: float       # SOL amount (always positive)
    price: float            # Price in SOL per token

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "signature": self.signature,
            "side": self.side,
            "token_mint": self.token_mint,
            "token_amount": self.token_amount,
            "sol_amount": self.sol_amount,
            "price": self.price
        }

    def to_mark(self, idx: int) -> Dict:
        """
        Convert to KLineChart mark format.

        Returns mark with International Standard:
        - Buy: Green "L" label (Long) - #26a69a
        - Sell: Red "S" label (Short) - #ef5350
        """
        is_buy = self.side == "buy"

        return {
            "id": idx,
            "time": self.timestamp * 1000,  # milliseconds
            "color": "#26a69a" if is_buy else "#ef5350",  # 国际标准: 买入=绿色, 卖出=红色
            "text": f"{self.side.upper()} {self.sol_amount:.4f} SOL",
            "label": "L" if is_buy else "S"
        }


def normalize_helius_transfer(
    transfer: Dict,
    wallet_address: str,
    sol_change: float,
    timestamp: int,
    signature: str,
    token_decimals: int = 9
) -> Optional[TradeRecord]:
    """
    Convert Helius token transfer to normalized TradeRecord.

    Args:
        transfer: Helius tokenTransfer object
        wallet_address: User's wallet address
        sol_change: SOL balance change (positive = received, negative = spent)
        timestamp: Transaction timestamp
        signature: Transaction signature
        token_decimals: Token decimals for amount normalization

    Returns:
        TradeRecord or None if not a relevant transfer
    """
    from_addr = transfer.get("fromUserAccount", "")
    to_addr = transfer.get("toUserAccount", "")
    mint = transfer.get("mint", "")
    raw_amount = transfer.get("tokenAmount", 0)

    # Determine trade direction
    if to_addr == wallet_address:
        side = "buy"
    elif from_addr == wallet_address:
        side = "sell"
    else:
        return None

    # Normalize amounts
    token_amount = normalize_amount(raw_amount, token_decimals)
    sol_amount = abs(sol_change)

    # Calculate price (SOL per token)
    price = sol_amount / token_amount if token_amount > 0 else 0

    return TradeRecord(
        timestamp=timestamp,
        signature=signature,
        side=side,
        token_mint=mint,
        token_amount=token_amount,
        sol_amount=sol_amount,
        price=price
    )


# =============================================================================
# Utility Functions
# =============================================================================

def get_cache_stats(mint_address: str) -> Dict:
    """
    Get statistics about cached K-line data.

    Returns:
        Dict with bar_count, first_time, last_time, file_size
    """
    path = get_kline_path(mint_address)

    if not path.exists():
        return {"bar_count": 0, "exists": False}

    klines = atomic_load(path, default=[])

    if not klines:
        return {"bar_count": 0, "exists": True, "empty": True}

    return {
        "bar_count": len(klines),
        "first_time": klines[0].get("timestamp") if klines else None,
        "last_time": klines[-1].get("timestamp") if klines else None,
        "file_size": path.stat().st_size,
        "exists": True
    }


# =============================================================================
# CLI Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PnLResearch V2.0 - Sync Engine Test")
    print("=" * 60)

    # Test atomic save/load
    test_data = [{"timestamp": 1234567890000, "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05, "volume": 1000}]
    test_path = CHART_LIBRARY_DIR / "_test_atomic.json"

    print("\n[Test] Atomic save...")
    success = atomic_save(test_path, test_data)
    print(f"  Save: {'OK' if success else 'FAIL'}")

    print("[Test] Atomic load...")
    loaded = atomic_load(test_path)
    print(f"  Load: {'OK' if loaded == test_data else 'FAIL'}")

    # Clean up
    if test_path.exists():
        test_path.unlink()

    # Test normalization
    print("\n[Test] Price normalization...")
    raw = 1000000000
    normalized = normalize_price(raw, 9)
    print(f"  {raw} / 10^9 = {normalized} {'OK' if normalized == 1.0 else 'FAIL'}")

    print("\n" + "=" * 60)
