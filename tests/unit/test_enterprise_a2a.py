import pytest
from app.protocol.contract_net import ContractNetNegotiator, AgentBid, cnp_negotiator
from app.protocol.resilience import ResilienceManager, CircuitBreaker, CircuitBreakerOpenException, CircuitState
from app.protocol.event_broker import AgentEventBroker, AgentEventMessage, event_broker


def test_contract_net_bidding():
    bids = [
        AgentBid(agent_id="analyst_1", estimated_latency_ms=200, cost_usd=0.01, confidence_score=0.95),
        AgentBid(agent_id="analyst_2", estimated_latency_ms=1000, cost_usd=0.05, confidence_score=0.70),
    ]
    eval_result = cnp_negotiator.evaluate_bids(bids)
    assert eval_result.selected_agent_id == "analyst_1"
    assert "analyst_1" in eval_result.reason


@pytest.mark.asyncio
async def test_resilience_circuit_breaker():
    res_mgr = ResilienceManager()
    agent_id = "failing_agent"

    async def fail_task():
        raise ValueError("Simulated network timeout")

    with pytest.raises(ValueError):
        await res_mgr.execute_with_retry(agent_id, fail_task, max_retries=3, base_delay_sec=0.01)

    # Circuit breaker should now be OPEN
    cb = res_mgr.get_circuit_breaker(agent_id)
    assert cb.state == CircuitState.OPEN

    # Next call should fail immediately with CircuitBreakerOpenException
    with pytest.raises(CircuitBreakerOpenException):
        await res_mgr.execute_with_retry(agent_id, fail_task, max_retries=1)

    # Verify message was logged in DLQ
    assert len(res_mgr.dead_letter_queue) > 0


def test_event_broker_traceparent():
    broker = AgentEventBroker()
    channel = "agent_auction_events"

    event = AgentEventMessage(
        sender_agent_id="coordinator",
        target_agent_id="auditor",
        performative="CFP",
        payload={"task": "financial_audit"},
    )

    broker.publish_event(channel, event)
    consumed = broker.consume_events(channel)

    assert len(consumed) == 1
    assert consumed[0].traceparent.startswith("00-")
    assert consumed[0].performative == "CFP"
