import random
import time
from enum import StrEnum
from typing import Any, Callable, Coroutine
from pydantic import BaseModel, Field


class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    pass


class CircuitBreaker:
    """Enterprise Circuit Breaker Pattern for Inter-Agent Communication."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_sec: float = 10.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_state_change >= self.recovery_timeout_sec:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = time.time()
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False


class DeadLetterMessage(BaseModel):
    message_id: str
    target_agent_id: str
    payload: dict[str, Any]
    error_reason: str
    timestamp: float = Field(default_factory=time.time)


class ResilienceManager:
    """Engine de Resiliência: Retry com Exponential Backoff + Jitter, Circuit Breaker e DLQ."""

    def __init__(self) -> None:
        self.breakers: dict[str, CircuitBreaker] = {}
        self.dead_letter_queue: list[DeadLetterMessage] = []

    def get_circuit_breaker(self, agent_id: str) -> CircuitBreaker:
        if agent_id not in self.breakers:
            self.breakers[agent_id] = CircuitBreaker()
        return self.breakers[agent_id]

    async def execute_with_retry(
        self,
        agent_id: str,
        func: Callable[[], Coroutine[Any, Any, Any]],
        max_retries: int = 3,
        base_delay_sec: float = 0.1,
    ) -> Any:
        cb = self.get_circuit_breaker(agent_id)
        if not cb.can_execute():
            raise CircuitBreakerOpenException(
                f"Circuito ABERTO para o agente '{agent_id}'. Requisição bloqueada por segurança."
            )

        last_exception = None
        for attempt in range(max_retries):
            try:
                result = await func()
                cb.record_success()
                return result
            except Exception as exc:
                last_exception = exc
                cb.record_failure()
                delay = random.uniform(0, min(2.0, base_delay_sec * (2 ** attempt)))
                time.sleep(delay)

        self.dead_letter_queue.append(
            DeadLetterMessage(
                message_id=f"msg_{time.time_ns()}",
                target_agent_id=agent_id,
                payload={},
                error_reason=str(last_exception),
            )
        )
        raise last_exception or RuntimeError(f"Falha de execução com agente '{agent_id}'.")


# Instância Singleton do Gerenciador de Resiliência
resilience_manager = ResilienceManager()
