import uuid
from typing import Any
from enum import StrEnum
from pydantic import BaseModel, Field


class Performative(StrEnum):
    CALL_FOR_PROPOSAL = "CFP"
    PROPOSE = "PROPOSE"
    REFUSE = "REFUSE"
    ACCEPT_PROPOSAL = "ACCEPT_PROPOSAL"
    REJECT_PROPOSAL = "REJECT_PROPOSAL"
    INFORM = "INFORM"
    FAILURE = "FAILURE"


class AgentBid(BaseModel):
    agent_id: str
    estimated_latency_ms: float
    cost_usd: float
    confidence_score: float = Field(ge=0.0, le=1.0)
    capabilities: list[str] = Field(default_factory=list)


class ProposalEvaluation(BaseModel):
    selected_agent_id: str
    winning_score: float
    reason: str
    all_bids: list[AgentBid]


class ContractNetNegotiator:
    """Enterprise Contract Net Protocol (FIPA CNP) Negotiator.
    
    Gerencia leilão distribuído de tarefas entre agentes, avaliando
    propostas com base em score ponderado (Confiança, Latência e Custo).
    """

    @staticmethod
    def evaluate_bids(
        bids: list[AgentBid],
        weight_confidence: float = 0.5,
        weight_latency: float = 0.3,
        weight_cost: float = 0.2,
    ) -> ProposalEvaluation:
        if not bids:
            raise ValueError("Nenhuma proposta recebida dos agentes para leilão.")

        best_score = -1.0
        best_agent = None

        for bid in bids:
            # Normalização simples de latência e custo
            latency_norm = max(0.1, 1.0 - (bid.estimated_latency_ms / 5000.0))
            cost_norm = max(0.1, 1.0 - (bid.cost_usd / 1.0))

            score = (
                (bid.confidence_score * weight_confidence)
                + (latency_norm * weight_latency)
                + (cost_norm * weight_cost)
            )

            if score > best_score:
                best_score = score
                best_agent = bid.agent_id

        return ProposalEvaluation(
            selected_agent_id=best_agent or bids[0].agent_id,
            winning_score=round(best_score, 4),
            reason=f"Agente {best_agent} selecionado via leilão FIPA CNP com score {best_score:.4f}.",
            all_bids=bids,
        )


# Instância Singleton do Negotiator
cnp_negotiator = ContractNetNegotiator()
