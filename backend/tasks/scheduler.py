import logging
from datetime import datetime, UTC
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.config import settings

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _scheduled_agent_run,
        CronTrigger.from_crontab(settings.agent_schedule_cron),
        id="daily_agent",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started, cron: %s", settings.agent_schedule_cron)


async def _scheduled_agent_run() -> None:
    from backend.database import SessionLocal
    from backend.models import AgentRun
    from backend.agent.orchestrator import run_agent

    db = SessionLocal()
    try:
        run = AgentRun(started_at=datetime.now(UTC), status="running")
        db.add(run)
        db.commit()
        db.refresh(run)
        await run_agent(run.id, db)
    except Exception as e:
        logger.error("Scheduled agent run failed: %s", e)
    finally:
        db.close()
