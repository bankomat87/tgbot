import uuid
from typing import Dict, Optional

class RenderConfig:
    @staticmethod
    def get_default_config(
        prompt: str,
        negative_prompt: str = None,
        style: str = "digital art"
    ) -> Dict:
        """Генерация конфига с параметрами по умолчанию"""
        return {
            'prompt': f"{prompt}, {style} style",
            'negative_prompt': negative_prompt or "low quality, blurry, bad anatomy",
            'seed': int(uuid.uuid4().hex[:8], 16) % 2**32,
            'use_stable_diffusion_model': 'neverendingDreamNED_v122BakedVae',
            'num_inference_steps': 25,
            'guidance_scale': 4.4,
            'width': 512,
            'height': 512,
            'sampler_name': 'euler',
            'scheduler_name': 'simple'
        }

    @staticmethod
    def validate_config(config: Dict) -> Optional[str]:
        """Валидация параметров"""
        if not config.get('prompt'):
            return "Prompt cannot be empty"
        if config['width'] % 64 != 0 or config['height'] % 64 != 0:
            return "Width and height must be multiples of 64"
        return None