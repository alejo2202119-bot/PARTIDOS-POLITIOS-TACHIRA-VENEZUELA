"""APScheduler-driven daily automation.

Schedules the ETL pipeline (``ETL_SCHEDULE_CRON``) and the executive PDF report
(``REPORT_DAILY_CRON``) in the configured timezone. Run as a long-lived worker:

    python -m app.etl.scheduler

Pass ``--once`` to execute the pipeline and report a single time and exit
(useful for cron-based deployments or manual runs).
"""

from __future__ import annotations

import asyncio
import logging
import sys

from app.config import settings
from app.etl import pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("vpid.etl.scheduler")


async def _job_pipeline() -> None:
    try:
        await pipeline.run_full()
    except Exception:
        logger.exception("ETL pipeline failed")


async def _job_report() -> None:
    try:
        await pipeline.run_daily_report()
    except Exception:
        logger.exception("Daily report generation failed")


async def run_once() -> None:
    """Run the pipeline then the report a single time."""
    await _job_pipeline()
    await _job_report()


def main() -> None:
    if "--once" in sys.argv:
        asyncio.run(run_once())
        return

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = AsyncIOScheduler(timezone=settings.APP_TIMEZONE)
    scheduler.add_job(_job_pipeline, CronTrigger.from_crontab(settings.ETL_SCHEDULE_CRON, timezone=settings.APP_TIMEZONE),
                      id="etl_pipeline", replace_existing=True)
    scheduler.add_job(_job_report, CronTrigger.from_crontab(settings.REPORT_DAILY_CRON, timezone=settings.APP_TIMEZONE),
                      id="daily_report", replace_existing=True)

    scheduler.start()
    logger.info("Scheduler started — ETL '%s', report '%s' (%s)",
                settings.ETL_SCHEDULE_CRON, settings.REPORT_DAILY_CRON, settings.APP_TIMEZONE)

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopping…")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
