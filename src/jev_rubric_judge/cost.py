"""Running cost of paid calls. Every caller reports token usage; the run stops when the budget is passed."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class CostMeter:
    name: str
    usd_per_m_input: float
    usd_per_m_output: float
    budget_usd: float
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def usd(self) -> float:
        return (self.input_tokens * self.usd_per_m_input + self.output_tokens * self.usd_per_m_output) / 1e6

    def add(self, input_tokens: int, output_tokens: int, reasoning_tokens: int = 0) -> None:
        with self._lock:
            self.calls += 1
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.reasoning_tokens += reasoning_tokens
            if self.usd > self.budget_usd:
                raise BudgetExceeded(f"{self.name}: ${self.usd:.4f} is over the budget ${self.budget_usd:.2f}")

    def summary(self) -> str:
        per_call = self.input_tokens / self.calls if self.calls else 0
        return (f"{self.name}: {self.calls} calls, {self.input_tokens} input tokens ({per_call:.0f} per call), "
                f"{self.output_tokens} output tokens, {self.reasoning_tokens} reasoning tokens, ${self.usd:.4f}")
