"""
Solscan Pro API 客户端
作为 Birdeye 的备用价格源
"""

import asyncio
import aiohttp
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SolscanPriceResult:
    """Solscan 价格查询结果"""
    success: bool
    value: Optional[float] = None
    timestamp: Optional[int] = None
    error: Optional[str] = None


class SolscanClient:
    """
    Solscan Pro API 客户端

    注意：Solscan Pro API 对历史价格查询支持有限
    主要用作 Birdeye 的备用数据源
    """

    BASE_URL = "https://pro-api.solscan.io/v2.0"
    SOL_MINT = "So11111111111111111111111111111111111111112"

    def __init__(self, api_token: str, requests_per_minute: int = 1000):
        """
        初始化 Solscan 客户端

        Args:
            api_token: Solscan Pro API Token
            requests_per_minute: 每分钟最大请求数 (Level 2 = 1000)
        """
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None
        self.requests_per_minute = requests_per_minute
        self.request_times: List[float] = []
        self.lock = asyncio.Lock()

        # 统计
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    async def _ensure_session(self):
        """确保 session 已初始化"""
        if self.session is None or self.session.closed:
            headers = {
                "token": self.api_token,
                "accept": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def close(self):
        """关闭 session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _rate_limit(self):
        """速率限制"""
        async with self.lock:
            now = time.time()
            self.request_times = [t for t in self.request_times if now - t < 60]

            if len(self.request_times) >= self.requests_per_minute:
                sleep_time = 60 - (now - self.request_times[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    self.request_times = []

            # 平滑请求
            min_interval = 60.0 / self.requests_per_minute
            if self.request_times:
                time_since_last = now - self.request_times[-1]
                if time_since_last < min_interval:
                    await asyncio.sleep(min_interval - time_since_last)

            self.request_times.append(time.time())

    async def get_token_price(
        self,
        address: str,
        from_time: int,
        to_time: Optional[int] = None,
        verbose: bool = False
    ) -> SolscanPriceResult:
        """
        获取代币在指定时间范围的价格

        Args:
            address: 代币地址
            from_time: 开始时间 (Unix 时间戳)
            to_time: 结束时间 (默认 from_time + 1)
            verbose: 是否输出详细日志

        Returns:
            SolscanPriceResult
        """
        await self._ensure_session()
        await self._rate_limit()

        self.total_requests += 1

        if to_time is None:
            to_time = from_time + 1

        if verbose:
            dt = datetime.fromtimestamp(from_time).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  [Solscan] 查询 {address[:8]}... @ {from_time} ({dt})")

        try:
            url = f"{self.BASE_URL}/token/price"
            params = {
                "address": address,
                "from_time": from_time,
                "to_time": to_time
            }

            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()

                    # 尝试多种响应格式
                    price = None

                    if isinstance(data, dict):
                        if "price" in data:
                            price = data.get("price")
                        elif "data" in data:
                            data_obj = data.get("data")
                            if isinstance(data_obj, dict):
                                price = data_obj.get("price")
                            elif isinstance(data_obj, list) and len(data_obj) > 0:
                                price = data_obj[0].get("price")
                        elif data.get("success") and data.get("data"):
                            items = data.get("data", [])
                            if isinstance(items, list) and len(items) > 0:
                                price = items[0].get("price") or items[0].get("value")

                    if price is not None:
                        self.successful_requests += 1
                        if verbose:
                            print(f"    ✅ 成功: ${float(price):.8f}")
                        return SolscanPriceResult(
                            success=True,
                            value=float(price),
                            timestamp=from_time
                        )
                    else:
                        self.failed_requests += 1
                        if verbose:
                            print(f"    ❌ 响应中未找到价格字段")
                        return SolscanPriceResult(
                            success=False,
                            error="API 响应中未找到价格数据"
                        )

                elif response.status == 403:
                    self.failed_requests += 1
                    return SolscanPriceResult(
                        success=False,
                        error="API Token 无效或权限不足 (403)"
                    )

                else:
                    self.failed_requests += 1
                    error_text = await response.text()
                    return SolscanPriceResult(
                        success=False,
                        error=f"HTTP {response.status}: {error_text[:100]}"
                    )

        except asyncio.TimeoutError:
            self.failed_requests += 1
            return SolscanPriceResult(success=False, error="请求超时")

        except Exception as e:
            self.failed_requests += 1
            return SolscanPriceResult(success=False, error=f"异常: {str(e)}")

    async def get_sol_price(self, timestamp: int, verbose: bool = False) -> SolscanPriceResult:
        """获取 SOL 在指定时间的价格"""
        return await self.get_token_price(self.SOL_MINT, timestamp, verbose=verbose)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{success_rate:.1f}%"
        }
