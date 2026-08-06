from unittest.mock import AsyncMock, Mock

import pytest

from app.business.analysis_service import AnalysisService


@pytest.mark.asyncio
async def test_process_image_saves_predictions_with_explainability(tmp_path):
    image_path = tmp_path / "cloud.jpg"
    image_path.write_bytes(b"image-bytes")
    ollama_client = Mock()
    ollama_client.analyze_image = AsyncMock(
        return_value=[{"label": "cumulus", "confidence": 0.91}]
    )
    ollama_client.get_explainability_boxes = AsyncMock(
        return_value=[{"label": "cumulus", "box_2d": [10, 20, 30, 40]}]
    )
    repository = Mock()
    service = AnalysisService(ollama_client=ollama_client, repository=repository)
    service._send_notification = Mock()

    await service.process_image(7, str(image_path), "fcm-token", explainability=True)

    repository.save_cloud_analysis.assert_called_once_with(
        7,
        [{"label": "cumulus", "confidence": 0.91, "box_2d": [10, 20, 30, 40]}],
    )
    repository.update_status.assert_called_once_with(7, "completed")
    service._send_notification.assert_called_once()


@pytest.mark.asyncio
async def test_process_image_marks_analysis_cancelled_on_error(tmp_path):
    image_path = tmp_path / "cloud.jpg"
    image_path.write_bytes(b"image-bytes")
    ollama_client = Mock()
    ollama_client.analyze_image = AsyncMock(side_effect=RuntimeError("ollama down"))
    repository = Mock()
    service = AnalysisService(ollama_client=ollama_client, repository=repository)
    service._send_notification = Mock()

    await service.process_image(7, str(image_path), explainability=False)

    repository.save_cloud_analysis.assert_not_called()
    repository.update_status.assert_called_once_with(7, "cancelled")
    service._send_notification.assert_called_once()
