"""
Birdeye API 客户端
专门用于获取 Solana 代币的历史价格

API 文档参考：
- Price - Historical by unix time: /defi/historical_price_unix
- Price - Historical: /defi/history_price
"""

import asyncio
import aiohttp
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BirdeyePriceResult:
    """Birdeye 价格查询结果"""
    success: bool
    value: Optional[float] = None          # USD 价格 (高精度，如 128.09276765626564)
    update_unix_time: Optional[int] = None  # 价格更新的 Unix 时间戳
    price_change_24h: Optional[float] = None  # 24小时价格变化百分比
    error: Optional[str] = None            # 错误信息


class RateLimiter:
    """
    速率限制器 - 防止触发 API 限制

    Birdeye Starter 版 ($99/月):
    - 15 rps (每秒15个请求)
    - 5M CUs/月
    """

    def __init__(self, max_per_minute: int = 800, min_interval: float = 0.08):
        """
        Args:
            max_per_minute: 每分钟最大请求数 (Starter版 15rps=900/min, 建议800)
            min_interval: 请求之间最小间隔秒数 (Starter版建议 0.08)
        """
        self.max_per_minute = max_per_minute
        self.min_interval = min_interval
        self.minute_requests: List[float] = []
        self.last_request_time: float = 0
        self.lock = asyncio.Lock()

    async def acquire(self):
        """获取请求许可"""
        async with self.lock:
            now = time.time()

            # 清理过期记录
            self.minute_requests = [r for r in self.minute_requests if now - r < 60]

            # 检查每分钟限制
            if len(self.minute_requests) >= self.max_per_minute:
                sleep_time = 60 - (now - self.minute_requests[0])
                if sleep_time > 0:
                    print(f"    [RateLimit] 达到每分钟限制，等待 {sleep_time:.1f} 秒...")
                    await asyncio.sleep(sleep_time)
                    self.minute_requests = []

            # 确保请求间隔
            time_since_last = now - self.last_request_time
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                await asyncio.sleep(wait_time)

            # 记录请求
            current_time = time.time()
            self.minute_requests.append(current_time)
            self.last_request_time = current_time


class BirdeyeClient:
    """
    Birdeye API 客户端

    支持的端点：
    1. /defi/historical_price_unix - 获取特定 Unix 时间戳的价格
    2. /defi/history_price - 获取时间范围内的价格历史
    3. /defi/price - 获取当前实时价格
    """

    BASE_URL = "https://public-api.birdeye.so"
    SOL_MINT = "So11111111111111111111111111111111111111112"

    def __init__(self, api_key: str, requests_per_minute: int = 800, min_interval: float = 0.08):
        """
        初始化 Birdeye 客户端

        Args:
            api_key: Birdeye API Key
            requests_per_minute: 每分钟最大请求数 (Starter版 15rps = 900/min, 建议800)
            min_interval: 请求最小间隔秒数 (Starter版 15rps, 建议 0.08秒)
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(max_per_minute=requests_per_minute, min_interval=min_interval)

        # 统计信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0

        # 简单缓存 (避免重复查询同一时间点)
        self._price_cache: Dict[str, BirdeyePriceResult] = {}

    async def _ensure_session(self):
        """确保 session 已初始化"""
        if self.session is None or self.session.closed:
            headers = {
                "accept": "application/json",
                "x-chain": "solana",
                "X-API-KEY": self.api_key
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def close(self):
        """关闭 session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Context manager entry - ensures session is initialized"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes session"""
        await self.close()
        return False

    def _make_cache_key(self, address: str, timestamp: int) -> str:
        """生成缓存键"""
        return f"{address}_{timestamp}"

    async def get_price_at_timestamp(
        self,
        address: str,
        timestamp: int,
        use_cache: bool = True,
        verbose: bool = False
    ) -> BirdeyePriceResult:
        """
        获取代币在特定 Unix 时间戳的价格

        使用 /defi/historical_price_unix 端点

        Args:
            address: 代币合约地址 (Mint Address)
            timestamp: 10位 Unix 时间戳 (秒)
            use_cache: 是否使用缓存
            verbose: 是否输出详细日志

        Returns:
            BirdeyePriceResult 包含价格或错误信息
        """
        # 确保 timestamp 是 10 位整数
        timestamp = int(timestamp)
        if timestamp > 10000000000:
            # 如果是 13 位毫秒时间戳，转换为秒
            timestamp = timestamp // 1000

        # 检查缓存
        cache_key = self._make_cache_key(address, timestamp)
        if use_cache and cache_key in self._price_cache:
            self.cache_hits += 1
            if verbose:
                print(f"  [Cache] 命中缓存: {address[:8]}... @ {timestamp}")
            return self._price_cache[cache_key]

        await self._ensure_session()
        await self.rate_limiter.acquire()

        self.total_requests += 1

        if verbose:
            dt = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  [Birdeye] 查询 {address[:8]}... @ {timestamp} ({dt})")

        try:
            url = f"{self.BASE_URL}/defi/historical_price_unix"
            params = {
                "address": address,
                "unixtime": timestamp
            }

            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("success") and data.get("data"):
                        price_data = data["data"]
                        result = BirdeyePriceResult(
                            success=True,
                            value=float(price_data.get("value", 0)),
                            update_unix_time=price_data.get("updateUnixTime"),
                            price_change_24h=price_data.get("priceChange24h")
                        )
                        self.successful_requests += 1

                        if use_cache:
                            self._price_cache[cache_key] = result

                        if verbose:
                            print(f"    ✅ 成功: ${result.value:.8f}")

                        return result
                    else:
                        # API 返回 success=false 或 data 为空
                        error_msg = data.get("message", "API 返回空数据")
                        self.failed_requests += 1

                        if verbose:
                            print(f"    ❌ 失败: {error_msg}")

                        return BirdeyePriceResult(success=False, error=error_msg)

                elif response.status == 401:
                    self.failed_requests += 1
                    error_text = await response.text()
                    return BirdeyePriceResult(
                        success=False,
                        error=f"API Key 无效或已过期 (401): {error_text[:100]}"
                    )

                elif response.status == 429:
                    self.failed_requests += 1
                    return BirdeyePriceResult(
                        success=False,
                        error="请求过于频繁，已触发速率限制 (429)"
                    )

                else:
                    self.failed_requests += 1
                    error_text = await response.text()
                    return BirdeyePriceResult(
                        success=False,
                        error=f"HTTP {response.status}: {error_text[:200]}"
                    )

        except asyncio.TimeoutError:
            self.failed_requests += 1
            return BirdeyePriceResult(success=False, error="请求超时")

        except Exception as e:
            self.failed_requests += 1
            return BirdeyePriceResult(success=False, error=f"异常: {str(e)}")

    async def get_price_history(
        self,
        address: str,
        time_from: int,
        time_to: int,
        interval: str = "1m",
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取代币在时间范围内的价格历史

        使用 /defi/history_price 端点

        Args:
            address: 代币合约地址
            time_from: 开始时间 (10位 Unix 时间戳)
            time_to: 结束时间 (10位 Unix 时间戳)
            interval: 时间间隔 (1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 8H, 12H, 1D, 3D, 1W, 1M)
            verbose: 是否输出详细日志

        Returns:
            价格历史列表 [{"unixTime": int, "value": float}, ...]
        """
        # 确保时间戳是 10 位
        time_from = int(time_from)
        time_to = int(time_to)
        if time_from > 10000000000:
            time_from = time_from // 1000
        if time_to > 10000000000:
            time_to = time_to // 1000

        await self._ensure_session()
        await self.rate_limiter.acquire()

        self.total_requests += 1

        if verbose:
            dt_from = datetime.fromtimestamp(time_from).strftime("%Y-%m-%d %H:%M:%S")
            dt_to = datetime.fromtimestamp(time_to).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  [Birdeye] 查询历史 {address[:8]}... | {dt_from} ~ {dt_to} | 间隔: {interval}")

        try:
            url = f"{self.BASE_URL}/defi/history_price"
            params = {
                "address": address,
                "address_type": "token",
                "type": interval,
                "time_from": time_from,
                "time_to": time_to
            }

            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("success") and data.get("data"):
                        items = data["data"].get("items", [])
                        self.successful_requests += 1

                        if verbose:
                            print(f"    ✅ 成功: 获取 {len(items)} 个价格点")

                        return items
                    else:
                        self.failed_requests += 1
                        if verbose:
                            print(f"    ❌ 失败: API 返回空数据")
                        return []

                else:
                    self.failed_requests += 1
                    if verbose:
                        error_text = await response.text()
                        print(f"    ❌ HTTP {response.status}: {error_text[:100]}")
                    return []

        except Exception as e:
            self.failed_requests += 1
            if verbose:
                print(f"    ❌ 异常: {e}")
            return []

    async def get_current_price(self, address: str, verbose: bool = False) -> BirdeyePriceResult:
        """
        获取代币当前实时价格

        使用 /defi/price 端点

        Args:
            address: 代币合约地址
            verbose: 是否输出详细日志

        Returns:
            BirdeyePriceResult
        """
        await self._ensure_session()
        await self.rate_limiter.acquire()

        self.total_requests += 1

        if verbose:
            print(f"  [Birdeye] 查询当前价格 {address[:8]}...")

        try:
            url = f"{self.BASE_URL}/defi/price"
            params = {"address": address}

            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("success") and data.get("data"):
                        price_data = data["data"]
                        result = BirdeyePriceResult(
                            success=True,
                            value=float(price_data.get("value", 0)),
                            update_unix_time=price_data.get("updateUnixTime"),
                            price_change_24h=price_data.get("priceChange24h")
                        )
                        self.successful_requests += 1

                        if verbose:
                            print(f"    ✅ 当前价格: ${result.value:.8f}")

                        return result
                    else:
                        self.failed_requests += 1
                        return BirdeyePriceResult(success=False, error="API 返回空数据")

                else:
                    self.failed_requests += 1
                    error_text = await response.text()
                    return BirdeyePriceResult(success=False, error=f"HTTP {response.status}: {error_text[:100]}")

        except Exception as e:
            self.failed_requests += 1
            return BirdeyePriceResult(success=False, error=f"异常: {str(e)}")

    async def get_sol_price_at_timestamp(self, timestamp: int, use_cache: bool = True, verbose: bool = False) -> BirdeyePriceResult:
        """
        获取 SOL 在特定时间戳的 USD 价格

        Args:
            timestamp: 10位 Unix 时间戳
            use_cache: 是否使用缓存
            verbose: 是否输出详细日志

        Returns:
            BirdeyePriceResult
        """
        return await self.get_price_at_timestamp(self.SOL_MINT, timestamp, use_cache, verbose)

    def get_statistics(self) -> Dict[str, Any]:
        """获取 API 调用统计"""
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "cache_hits": self.cache_hits,
            "success_rate": f"{success_rate:.1f}%"
        }

    def print_statistics(self):
        """打印 API 调用统计"""
        stats = self.get_statistics()
        print(f"\n{'='*60}")
        print(f"Birdeye API 调用统计")
        print(f"{'='*60}")
        print(f"  总请求数:    {stats['total_requests']}")
        print(f"  成功:        {stats['successful_requests']}")
        print(f"  失败:        {stats['failed_requests']}")
        print(f"  缓存命中:    {stats['cache_hits']}")
        print(f"  成功率:      {stats['success_rate']}")
        print(f"{'='*60}\n")

    def clear_cache(self):
        """清除价格缓存"""
        self._price_cache.clear()
        self.cache_hits = 0

    async def get_ohlcv(
        self,
        address: str,
        time_from: int,
        time_to: int,
        interval: str = "1m",
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取代币 OHLCV K线数据

        使用 /defi/ohlcv 端点

        Args:
            address: 代币合约地址
            time_from: 开始时间 (10位 Unix 时间戳)
            time_to: 结束时间 (10位 Unix 时间戳)
            interval: 时间间隔 (1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 8H, 12H, 1D, 3D, 1W, 1M)
            verbose: 是否输出详细日志

        Returns:
            OHLCV 数据列表 [{"o": open, "h": high, "l": low, "c": close, "v": volume, "unixTime": int}, ...]
        """
        # 确保时间戳是 10 位
        time_from = int(time_from)
        time_to = int(time_to)
        if time_from > 10000000000:
            time_from = time_from // 1000
        if time_to > 10000000000:
            time_to = time_to // 1000

        await self._ensure_session()
        await self.rate_limiter.acquire()

        self.total_requests += 1

        if verbose:
            dt_from = datetime.fromtimestamp(time_from).strftime("%Y-%m-%d %H:%M:%S")
            dt_to = datetime.fromtimestamp(time_to).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  [Birdeye] OHLCV {address[:8]}... | {dt_from} ~ {dt_to} | {interval}")

        try:
            url = f"{self.BASE_URL}/defi/ohlcv"
            params = {
                "address": address,
                "type": interval,
                "time_from": time_from,
                "time_to": time_to
            }

            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("success") and data.get("data"):
                        items = data["data"].get("items", [])
                        self.successful_requests += 1

                        if verbose:
                            print(f"    OK: {len(items)} candles")
                            # DEBUG: 打印前3条原始数据
                            if items:
                                print(f"    [RAW] First item: {items[0]}")
                                if len(items) > 1:
                                    print(f"    [RAW] Second item: {items[1]}")

                        return items
                    else:
                        self.failed_requests += 1
                        if verbose:
                            print(f"    FAILED: Empty data")
                        return []

                else:
                    self.failed_requests += 1
                    if verbose:
                        error_text = await response.text()
                        print(f"    HTTP {response.status}: {error_text[:100]}")
                    return []

        except Exception as e:
            self.failed_requests += 1
            if verbose:
                print(f"    Exception: {e}")
            return []
