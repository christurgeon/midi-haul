import asyncio
import json
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db, SessionLocal
from backend.models import AgentRun, AgentRunStep
from backend.schemas import AgentRunSchema

router = APIRouter(tags=["agent"])


@router.post("/run")
def trigger_agent_run(db: Session = Depends(get_db)):
    run = AgentRun(started_at=datetime.now(UTC), status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    import asyncio
    from fastapi import BackgroundTasks
    from backend.agent.orchestrator import run_agent

    async def _run():
        db2 = SessionLocal()
        try:
            await run_agent(run.id, db2)
        finally:
            db2.close()

    asyncio.ensure_future(_run())
    return {"run_id": run.id}


@router.get("/runs", response_model=list[AgentRunSchema])
def list_runs(db: Session = Depends(get_db)):
    return db.query(AgentRun).order_by(AgentRun.started_at.desc()).limit(20).all()


@router.get("/runs/{run_id}", response_model=AgentRunSchema)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    return run


@router.get("/runs/{run_id}/stream")
async def stream_run(run_id: int):
    """Server-Sent Events stream of agent run steps."""

    async def event_generator():
        last_step_id = 0
        while True:
            db = SessionLocal()
            try:
                run = db.get(AgentRun, run_id)
                if not run:
                    yield f"data: {json.dumps({'error': 'run not found'})}\n\n"
                    return

                new_steps = (
                    db.query(AgentRunStep)
                    .filter(AgentRunStep.run_id == run_id, AgentRunStep.id > last_step_id)
                    .order_by(AgentRunStep.id)
                    .all()
                )

                for step in new_steps:
                    last_step_id = step.id
                    payload = {
                        "id": step.id,
                        "tool_name": step.tool_name,
                        "tool_input": step.tool_input,
                        "tool_result": step.tool_result,
                        "executed_at": step.executed_at.isoformat(),
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                if run.status in ("completed", "failed"):
                    yield f"data: {json.dumps({'done': True, 'status': run.status})}\n\n"
                    return

            finally:
                db.close()

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
