"""
LangSmith tracing client and context managers
"""

import json
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from langsmith import Client

from app.config import settings

logger = logging.getLogger(__name__)

# Global LangSmith client instance
_langsmith_client: Optional[Client] = None


def get_langsmith_client() -> Optional[Client]:
    """
    Get or initialize LangSmith client.
    Returns None if tracing is disabled or API key is not set.
    """
    global _langsmith_client
    
    tracing_enabled = getattr(settings, "LANGSMITH_TRACING_ENABLED", getattr(settings, "langsmith_tracing_enabled", False))
    if not tracing_enabled:
        return None
    
    api_key = getattr(settings, "LANGSMITH_API_KEY", getattr(settings, "langsmith_api_key", None))
    if not api_key:
        logger.warning("LANGSMITH_API_KEY not set, tracing disabled")
        return None
    
    project = getattr(settings, "LANGSMITH_PROJECT", getattr(settings, "langsmith_project", "smartreco-prod"))
    if _langsmith_client is None:
        try:
            _langsmith_client = Client(api_key=api_key)
            logger.info(f"LangSmith client initialized for project: {project}")
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith client: {e}")
            return None
    
    return _langsmith_client



@contextmanager
def trace_run(
    name: str,
    run_type: str,
    inputs: Dict[str, Any],
    parent_run_id: Optional[str] = None,
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Context manager for tracing a run in LangSmith.
    
    Args:
        name: Name of the run (e.g., "behavior_analysis")
        run_type: Type of run ("chain", "llm", "retriever", "tool")
        inputs: Input data for the run
        parent_run_id: Optional parent run ID for nesting
        tags: Optional list of tags
        metadata: Optional metadata dict
    
    Yields:
        run_id: The LangSmith run ID (or None if tracing disabled)
    
    Usage:
        with trace_run("my_agent", "chain", {"user_id": 123}) as run_id:
            result = do_work()
            # result will be automatically captured as output
            yield result  # or return result
    """
    client = get_langsmith_client()
    
    if client is None:
        # Tracing disabled, yield None and continue
        yield None
        return
    
    run_id = None
    outputs = None
    error = None
    start_time = datetime.utcnow()
    
    import concurrent.futures
    _executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    try:
        # Create run in background thread to avoid blocking network I/O
        try:
            future = _executor.submit(
                client.create_run,
                name=name,
                run_type=run_type,
                inputs=inputs,
                project_name=getattr(settings, "langsmith_project", "smartreco-prod"),
                parent_run_id=parent_run_id,
                tags=tags or [],
                extra=metadata or {}
            )
            run = future.result(timeout=1.0)
            run_id = getattr(run, "id", None) if run else None
            logger.debug(f"Created LangSmith run: {name} (ID: {run_id})")
        except Exception as e:
            logger.warning(f"LangSmith create_run non-fatal timeout/error '{name}': {e}")
            run_id = None
        
        # Yield control back to caller
        result = yield run_id
        
        # Capture outputs if provided
        if result is not None:
            outputs = result if isinstance(result, dict) else {"result": result}
        
    except Exception as exc:
        error = str(exc)
        logger.error(f"Error in traced execution block {name}: {error}")
        raise
    
    finally:
        # Update run with outputs and end time in background
        if run_id and client:
            try:
                end_time = datetime.utcnow()
                _executor.submit(
                    client.update_run,
                    run_id=run_id,
                    outputs=outputs or {},
                    end_time=end_time,
                    error=error
                )
                latency_ms = (end_time - start_time).total_seconds() * 1000
                logger.debug(f"Completed LangSmith run: {name} ({latency_ms:.2f}ms)")
            except Exception as e:
                logger.error(f"Failed to update LangSmith run {run_id}: {e}")


def list_recent_runs(limit: int = 50, status: Optional[str] = None) -> list:
    """
    Fetch recent runs from LangSmith project.
    
    Args:
        limit: Maximum number of runs to fetch
        status: Optional filter by status ("success", "error", "pending")
    
    Returns:
        List of run dictionaries
    """
    client = get_langsmith_client()
    
    if client is None:
        return []
    
    try:
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        
        runs = client.list_runs(
            project_name=settings.langsmith_project,
            limit=limit,
            filter=json.dumps(filter_dict) if filter_dict else None
        )
        
        # Convert runs to dicts
        result = []
        for run in runs:
            trace_record = {
                "run_id": str(run.id),
                "name": run.name,
                "run_type": run.run_type,
                "status": "success" if run.error is None else "error" if run.error else "pending",
                "latency_ms": (run.end_time - run.start_time).total_seconds() * 1000 if run.end_time and run.start_time else 0,
                "timestamp": run.start_time.isoformat() if run.start_time else None,
                "inputs": run.inputs,
                "outputs": run.outputs,
                "error": run.error,
                "url": run.url if hasattr(run, 'url') else None,
            }
            
            # Extract token usage if present
            if hasattr(run, 'extra') and run.extra:
                usage = run.extra.get('usage_metadata', {})
                trace_record["token_usage"] = usage.get('total_tokens', 0)
                trace_record["prompt_tokens"] = usage.get('prompt_tokens', 0)
                trace_record["completion_tokens"] = usage.get('completion_tokens', 0)
                trace_record["total_cost"] = usage.get('total_cost', 0)
            else:
                trace_record["token_usage"] = 0
                trace_record["prompt_tokens"] = 0
                trace_record["completion_tokens"] = 0
                trace_record["total_cost"] = 0
            
            result.append(trace_record)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list LangSmith runs: {e}")
        return []

