from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date


@dataclass
class RateLimitDecision:
    allowed: bool
    attempts_used: int
    daily_limit: int


class DailyBasicAnalysisLimiter:
    def __init__(self, daily_limit: int = 2) -> None:
        self.daily_limit = daily_limit
        self._attempts: dict[tuple[str, date], int] = defaultdict(int)

    def check_and_record(self, ip_address: str) -> RateLimitDecision:
        today = date.today()
        key = (ip_address, today)
        current = self._attempts[key]
        if current >= self.daily_limit:
            return RateLimitDecision(allowed=False, attempts_used=current, daily_limit=self.daily_limit)
        self._attempts[key] = current + 1
        return RateLimitDecision(allowed=True, attempts_used=self._attempts[key], daily_limit=self.daily_limit)


rate_limit_service = DailyBasicAnalysisLimiter()
