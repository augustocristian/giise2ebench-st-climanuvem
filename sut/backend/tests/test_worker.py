import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from app.business import worker
from app.infrastructure.queue import AnalysisTask


@dataclass
class FakeQueue:
    task: AnalysisTask

    def __post_init__(self):
        self.task_done_calls = 0

    async def get(self):
        if self.task_done_calls:
            await asyncio.sleep(60)
        return self.task

    def task_done(self):
        self.task_done_calls += 1


async def run_worker_until_processed(fake_queue: FakeQueue):
    task = asyncio.create_task(worker.analysis_worker())
    for _ in range(50):
        if fake_queue.task_done_calls:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            return
        await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    raise AssertionError("worker did not process the queued task")


@pytest.mark.asyncio
async def test_worker_processes_active_analysis(monkeypatch):
    fake_queue = FakeQueue(AnalysisTask(analysis_id=1, file_path="/tmp/cloud.jpg", fcm_token="fcm", explainability=True))
    process_image = AsyncMock()

    monkeypatch.setattr(worker, "analysis_queue", fake_queue)
    monkeypatch.setattr(worker, "AnalysisRepository", lambda: type("Repo", (), {"get_analysis_status": lambda self, _id: "analyzing"})())
    monkeypatch.setattr(worker, "AnalysisService", lambda: type("Service", (), {"process_image": process_image})())

    await run_worker_until_processed(fake_queue)

    process_image.assert_awaited_once_with(1, "/tmp/cloud.jpg", "fcm", True)
    assert fake_queue.task_done_calls == 1


@pytest.mark.asyncio
async def test_worker_skips_cancelled_or_deleted_analysis(monkeypatch):
    fake_queue = FakeQueue(AnalysisTask(analysis_id=2, file_path="/tmp/cloud.jpg", fcm_token=None, explainability=False))
    process_image = AsyncMock()

    monkeypatch.setattr(worker, "analysis_queue", fake_queue)
    monkeypatch.setattr(worker, "AnalysisRepository", lambda: type("Repo", (), {"get_analysis_status": lambda self, _id: "cancelled"})())
    monkeypatch.setattr(worker, "AnalysisService", lambda: type("Service", (), {"process_image": process_image})())

    await run_worker_until_processed(fake_queue)

    process_image.assert_not_awaited()
    assert fake_queue.task_done_calls == 1


@pytest.mark.asyncio
async def test_worker_marks_task_done_when_processing_raises(monkeypatch):
    fake_queue = FakeQueue(AnalysisTask(analysis_id=3, file_path="/tmp/cloud.jpg", fcm_token=None, explainability=False))
    process_image = AsyncMock(side_effect=RuntimeError("processing failed"))

    monkeypatch.setattr(worker, "analysis_queue", fake_queue)
    monkeypatch.setattr(worker, "AnalysisRepository", lambda: type("Repo", (), {"get_analysis_status": lambda self, _id: "analyzing"})())
    monkeypatch.setattr(worker, "AnalysisService", lambda: type("Service", (), {"process_image": process_image})())

    await run_worker_until_processed(fake_queue)

    process_image.assert_awaited_once()
    assert fake_queue.task_done_calls == 1


@pytest.mark.asyncio
async def test_worker_propagates_cancellation(monkeypatch):
    class CancelQueue:
        async def get(self):
            raise asyncio.CancelledError()

    monkeypatch.setattr(worker, "analysis_queue", CancelQueue())

    with pytest.raises(asyncio.CancelledError):
        await worker.analysis_worker()
