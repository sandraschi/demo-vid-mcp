"""Persistent background job queue for demo video generation."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

from demo_vid_mcp.config import config

logger = logging.getLogger("demo-vid-mcp.queue")


class JobQueue:
    def __init__(self, queue_file: Path | None = None) -> None:
        self.queue_file = queue_file or (Path(config.data_dir) / "queue.json")
        self._jobs: dict[str, dict[str, Any]] = {}
        self._work_queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None
        self._load()

    def _load(self) -> None:
        if self.queue_file.exists():
            try:
                data = json.loads(self.queue_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._jobs = data
            except Exception as e:
                logger.warning("Failed to load queue state from %s: %s", self.queue_file, e)
                self._jobs = {}

    def _save(self) -> None:
        try:
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            self.queue_file.write_text(json.dumps(self._jobs, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to persist queue state to %s: %s", self.queue_file, e)

    def enqueue(
        self,
        repo: str,
        script_yaml: str | None = None,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
    ) -> dict[str, Any]:
        """Add a video generation job to the persistent queue."""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        job = {
            "id": job_id,
            "repo": repo,
            "script_yaml": script_yaml,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "status": "pending",
            "created_at": int(time.time()),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
        }
        self._jobs[job_id] = job
        self._save()
        self._work_queue.put_nowait(job_id)
        logger.info("Enqueued job %s for repo '%s'", job_id, repo)
        return job

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return list of jobs sorted by created_at descending."""
        jobs = sorted(self._jobs.values(), key=lambda j: j.get("created_at", 0), reverse=True)
        return jobs[:limit]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        job = self._jobs.get(job_id)
        if not job:
            return False
        if job["status"] == "pending":
            job["status"] = "canceled"
            job["completed_at"] = int(time.time())
            self._save()
            logger.info("Canceled job %s", job_id)
            return True
        return False

    async def start_worker(self) -> None:
        """Start the background worker if not already running."""
        if self._worker_task is None or self._worker_task.done():
            # Re-enqueue any jobs that were pending on restart
            for j in self._jobs.values():
                if j.get("status") == "pending":
                    self._work_queue.put_nowait(j["id"])
            self._worker_task = asyncio.create_task(self._process_queue())

    async def _process_queue(self) -> None:
        """Sequential FIFO worker processing jobs."""
        from demo_vid_mcp.tools.generate import demo_vid_generate

        while True:
            try:
                job_id = await self._work_queue.get()
                job = self._jobs.get(job_id)
                if not job or job["status"] != "pending":
                    self._work_queue.task_done()
                    continue

                job["status"] = "running"
                job["started_at"] = int(time.time())
                self._save()
                logger.info("Running queue job %s (repo=%s)...", job_id, job["repo"])

                try:
                    result = await demo_vid_generate(
                        repo=job["repo"],
                        script_yaml=job.get("script_yaml"),
                    )
                    job["result"] = result
                    if result.get("success"):
                        job["status"] = "completed"
                    else:
                        job["status"] = "failed"
                        job["error"] = result.get("error", "Generation failed")
                except Exception as e:
                    job["status"] = "failed"
                    job["error"] = str(e)
                finally:
                    job["completed_at"] = int(time.time())
                    self._save()
                    self._work_queue.task_done()
                    logger.info("Completed job %s with status %s", job_id, job["status"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Queue worker error: %s", e)
                await asyncio.sleep(1)


# Global singleton queue instance
job_queue = JobQueue()
