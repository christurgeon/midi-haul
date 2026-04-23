import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC
from backend.agent.tools import TOOLS


def test_tools_count():
    assert len(TOOLS) == 6


def test_tools_have_required_fields():
    required_names = {"list_known_sources", "run_scraper", "run_crawler", "search_web_for_midi_sources", "get_scrape_errors", "log_message"}
    actual_names = {t["name"] for t in TOOLS}
    assert actual_names == required_names
    for tool in TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool


def test_run_scraper_tool_schema():
    tool = next(t for t in TOOLS if t["name"] == "run_scraper")
    props = tool["input_schema"]["properties"]
    assert "source" in props
    assert "max_files" in props
    assert tool["input_schema"]["required"] == ["source"]


@pytest.mark.asyncio
async def test_run_agent_handles_end_turn(db):
    from backend.models import AgentRun
    from backend.agent.orchestrator import run_agent

    run = AgentRun(started_at=datetime.now(UTC), status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = []

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("backend.agent.orchestrator.anthropic.AsyncAnthropic", return_value=mock_client):
        await run_agent(run.id, db)

    db.refresh(run)
    assert run.status == "completed"
    assert run.finished_at is not None
