import asyncio
import logging
from app.infrastructure.queue import analysis_queue, AnalysisTask
from app.business.analysis_service import AnalysisService
from app.data.analysis_repository import AnalysisRepository

logger = logging.getLogger(__name__)

async def analysis_worker():
    """
    Background worker that continuously processes analysis tasks from the queue sequentially.
    """
    logger.info("Starting analysis worker...")
    
    while True:
        try:
            task: AnalysisTask = await analysis_queue.get()
            logger.info(f"Worker picked up task for analysis_id: {task.analysis_id}")
            
            try:
                status = AnalysisRepository().get_analysis_status(task.analysis_id)
                is_cancelled_or_deleted = status is None or status == 'cancelled'
                
                if is_cancelled_or_deleted:
                    logger.info(f"Analysis {task.analysis_id} was deleted or cancelled, skipping...")
                else:
                    service = AnalysisService()
                    await service.process_image(task.analysis_id, task.file_path, task.fcm_token, task.explainability)
            except Exception as e:
                logger.exception(f"Error processing analysis {task.analysis_id} in worker: {e}")
            finally:
                analysis_queue.task_done()
                logger.info(f"Worker finished processing analysis_id: {task.analysis_id}")
                
        except asyncio.CancelledError:
            logger.info("Analysis worker cancelled, shutting down...")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in worker loop: {e}")
            # Prevent rapid spinning if something goes horribly wrong
            await asyncio.sleep(1)
