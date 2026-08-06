import base64
import logging
import anyio
from firebase_admin import messaging
from app.infrastructure.ollama_client import OllamaClient
from app.data.analysis_repository import AnalysisRepository

logger = logging.getLogger(__name__)

class AnalysisService:
    
    def __init__(self, ollama_client=None, repository=None):
        self.ollama_client = ollama_client or OllamaClient()
        self.repository = repository or AnalysisRepository()

    async def process_image(self, analysis_id: int, file_path: str, fcm_token: str = "", explainability: bool = False):
        try:
            logger.info(
                "Starting analysis process for analysis_id=%s explainability=%s file_path=%s",
                analysis_id,
                explainability,
                file_path,
            )
            # 1. Leer imagen y convertir a base64
            async with await anyio.open_file(file_path, "rb") as f:
                content = await f.read()
                img_b64 = base64.b64encode(content).decode('utf-8')
            
            # 2. Llamada a Ollama (Paso 1: Clasificación Simple)
            predictions = await self.ollama_client.analyze_image(img_b64)
            
            # 3. Paso 2: Explicabilidad (si aplica)
            if explainability and predictions and any(p.get('label') != 'no_cloud' for p in predictions):
                try:
                    labels = [p['label'] for p in predictions if p.get('label') != 'no_cloud']
                    boxes = await self.ollama_client.get_explainability_boxes(img_b64, labels)
                    
                    # Combinar cajas con predicciones
                    for pred in predictions:
                        label = pred.get('label')
                        # Buscar la caja correspondiente
                        box_match = next((b.get('box_2d') for b in boxes if b.get('label') == label), None)
                        if box_match:
                            pred['box_2d'] = box_match
                except Exception as e:
                    logger.warning("Explainability failed for analysis_id=%s: %s", analysis_id, e)
                    # Continuamos con las predicciones sin cajas si falla el segundo paso
            
            # 4. Guardar resultados y actualizar estado a completado exitosamente
            self.repository.save_cloud_analysis(analysis_id, predictions)
            self.repository.update_status(analysis_id, 'completed')
            logger.info("Analysis completed successfully for analysis_id=%s", analysis_id)
            self._send_notification(fcm_token, analysis_id, "Análisis Completado", "Tu imagen de nubes ha sido analizada con éxito.")
            
        except Exception as e:
            logger.exception("Error processing analysis_id=%s: %s", analysis_id, e)
            # 5. En caso de error, marcar como cancelado
            self.repository.update_status(analysis_id, 'cancelled')
            self._send_notification(fcm_token, analysis_id, "Error en el Análisis", "Hubo un problema al procesar tu imagen. Abre para más detalles.")

    def _send_notification(self, fcm_token: str, analysis_id: int, title: str, body: str):
        if not fcm_token:
            return
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    "analysis_id": str(analysis_id)
                },
                token=fcm_token,
            )
            response = messaging.send(message)
            logger.info("Successfully sent FCM notification for analysis_id=%s response=%s", analysis_id, response)
        except Exception as e:
            logger.exception("Error sending FCM notification for analysis_id=%s: %s", analysis_id, e)
