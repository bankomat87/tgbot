import requests
import uuid
import logging
import asyncio
import base64
from typing import Dict, Optional, Tuple
from config import API_BASE_URL

logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self):
        self.api_url = API_BASE_URL
        self.timeout = 60
        self.max_retries = 3

    async def check_api_status(self) -> Tuple[bool, str]:
        """Проверка доступности API и состояния GPU"""
        try:
            response = requests.get(f"{self.api_url}/ping", timeout=5)
            if response.status_code == 200:
                data = response.json()
                vram_free = data["devices"]["active"]["cuda"]["mem_free"]
                status = (
                    f"🟢 API онлайн | GPU: {data['devices']['active']['cuda']['name']}\n"
                    f"Свободно VRAM: {vram_free:.1f}GB"
                )
                return True, status
            return False, f"API вернул код {response.status_code}"
        except Exception as e:
            logger.error(f"API check failed: {str(e)}", exc_info=True)
            return False, f"Ошибка подключения: {str(e)}"

    async def generate_image(self, prompt: str, style: str) -> Dict:
        """Запуск генерации изображения со всеми параметрами"""
        try:
            params = {
                "prompt": prompt,
                "negative_prompt": "low quality, blurry",
                "seed": int(uuid.uuid4().hex[:8], 16) % 2**32,
                "use_stable_diffusion_model": "neverendingDreamNED_v122BakedVae",
                "use_vae_model": "",
                "clip_skip": False,
                "num_inference_steps": 25,
                "guidance_scale": 4.4,
                "distilled_guidance_scale": 3.5,
                "width": 512,
                "height": 512,
                "sampler_name": "euler",
                "scheduler_name": "simple",
                "use_controlnet_model": None,
                "control_alpha": None,
                "use_embeddings_model": None,
                "use_lora_model": None,
                "use_face_correction": None,
                "use_upscale": None,
                "tiling": None,
                "task_id": str(uuid.uuid4())
            }

            # Удаляем None-значения, если API их не принимает
            params = {k: v for k, v in params.items() if v is not None}

            # Браузерные заголовки
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": f"{self.api_url}/",
                "Origin": self.api_url
            }

            for attempt in range(self.max_retries):
                try:
                    response = requests.post(
                        f"{self.api_url}/render",
                        json=params,
                        headers=headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "task_id": params["task_id"],
                            "estimated_time": params["num_inference_steps"] * 2
                        }
                    
                    logger.warning(
                        f"Attempt {attempt + 1}: API returned {response.status_code}. "
                        f"Response: {response.text}"
                    )
                
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
            
            return {
                "success": False,
                "error": f"Не удалось запустить генерацию после {self.max_retries} попыток"
            }

        except Exception as e:
            logger.error(f"Generation failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_image(self, task_id: str) -> Optional[bytes]:
        """Получение сгенерированного изображения через base64 декодирование"""
        try:
            response = requests.get(
                f"{self.api_url}/image/stream/{task_id}/0",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    
                    # Проверяем структуру ответа
                    if 'output' not in json_data or len(json_data['output']) == 0:
                        logger.error("Invalid response structure: missing 'output' field")
                        return None
                    
                    # Извлекаем base64 данные
                    img_data = json_data['output'][0].get('data', '')
                    if not img_data:
                        logger.error("No image data found in response")
                        return None
                    
                    # Удаляем префикс data:image/png;base64, если есть
                    if ',' in img_data:
                        img_data = img_data.split(',')[1]
                    
                    # Декодируем base64
                    return base64.b64decode(img_data)
                    
                except (KeyError, IndexError, ValueError, TypeError) as e:
                    logger.error(f"Failed to parse image data: {str(e)}", exc_info=True)
                    return None
                except base64.binascii.Error as e:
                    logger.error(f"Base64 decoding failed: {str(e)}")
                    return None
                
            logger.warning(
                f"Failed to fetch image. Status: {response.status_code}. "
                f"Response: {response.text}"
            )
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return None