import logging
from typing import Any, Dict, Optional
from app.config import settings

logger = logging.getLogger("a2a_observability")

try:
    from langfuse import Langfuse
    langfuse_client = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
    )
except Exception as e:
    logger.warning(f"Could not initialize Langfuse client: {e}")
    langfuse_client = None


def _create_trace(
    name: str,
    session_id: Optional[str] = None,
    tags: Optional[list] = None,
    input_data: Optional[Any] = None,
    metadata: Optional[dict] = None
) -> Any:
    if not langfuse_client:
        return None
    try:
        if hasattr(langfuse_client, "trace"):
            return langfuse_client.trace(
                name=name,
                session_id=session_id,
                tags=tags,
                input=input_data,
                metadata=metadata
            )
        elif hasattr(langfuse_client, "start_observation"):
            return langfuse_client.start_observation(
                name=name,
                type="TRACE",
                session_id=session_id,
                tags=tags,
                input=input_data,
                metadata=metadata
            )
    except Exception as e:
        logger.warning(f"Error creating Langfuse trace: {e}")
    return None


class A2AObservability:
    @staticmethod
    def trace_handshake(agent_role: str, capabilities: Any) -> Any:
        return _create_trace(
            name="a2a_handshake",
            tags=["a2a-protocol", f"role:{agent_role}", "handshake"],
            metadata={"agent_role": agent_role, "capabilities": capabilities}
        )

    @staticmethod
    def trace_task_delegation(
        task_id: str,
        source_agent: str,
        target_agent: str,
        task_type: str,
        payload: Dict[str, Any]
    ) -> Any:
        return _create_trace(
            name="a2a_task_delegation",
            session_id=task_id,
            tags=["a2a-protocol", f"from:{source_agent}", f"to:{target_agent}", f"type:{task_type}"],
            input_data={"source": source_agent, "target": target_agent, "task_type": task_type, "payload": payload},
            metadata={"task_id": task_id}
        )

    @staticmethod
    def record_span(
        trace: Any,
        span_name: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        level: str = "DEFAULT"
    ):
        if not trace:
            return None
        try:
            if hasattr(trace, "span"):
                span = trace.span(name=span_name, input=input_data)
                if output_data and hasattr(span, "end"):
                    span.end(output=output_data, level=level)
                return span
        except Exception as e:
            logger.warning(f"Error recording span: {e}")
        return None

    @staticmethod
    def flush():
        if langfuse_client and hasattr(langfuse_client, "flush"):
            try:
                langfuse_client.flush()
            except Exception:
                pass
