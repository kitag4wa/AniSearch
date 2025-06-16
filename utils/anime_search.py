import aiohttp
import base64
import logging
from typing import List, Dict, Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)

API_URL = "https://api.trace.moe/search"
ANILIST_URL = "https://api.trace.moe/anilist"
MAX_IMAGE_SIZE = 10 * 1024 * 1024


def compress_image(image_data: bytes, max_size: int = MAX_IMAGE_SIZE):

    try:

        if len(image_data) <= max_size:
            return image_data
        
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode in ('RGBA', 'P', 'LA'):
            image = image.convert('RGB')
        
        for quality in [85, 70, 55, 40]:
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_data = output.getvalue()
            
            if len(compressed_data) <= max_size:
                return compressed_data
        
        width, height = image.size
        for scale in [0.8, 0.6, 0.4]:
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            resized_image.save(output, format='JPEG', quality=70, optimize=True)
            compressed_data = output.getvalue()
            
            if len(compressed_data) <= max_size:
                return compressed_data
        
        return image_data
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return image_data


async def search_anime(image_data: bytes):
    try:
        try:
            img = Image.open(io.BytesIO(image_data))
            
            if img.mode in ['RGBA', 'LA', 'P', 'CMYK']:
                img = img.convert('RGB')
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            jpeg_data = output.getvalue()
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            jpeg_data = image_data
        
        if len(jpeg_data) > 5 * 1024 * 1024:
            jpeg_data = compress_image(jpeg_data)
        
        try:
            params = {
                'anilistInfo': 'true', 
                'cutBorders': 'true'  
            }
            
            form_data = aiohttp.FormData()
            form_data.add_field(
                'image', 
                jpeg_data, 
                filename='image.jpg',
                content_type='image/jpeg'
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_URL,
                    params=params,
                    data=form_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        if not data.get('error'):
                            results = data.get('result', [])
                            
                            filtered_results = [
                                r for r in results 
                                if r.get('similarity', 0) > 0.87
                            ]
                            
                            return filtered_results if filtered_results else results[:3]
                    else:
                        logger.warning(f"статус {response.status}")
                        
        except Exception as e:
            logger.warning(f"Ошибка: {e}")
        
        try:
            image_base64 = base64.b64encode(jpeg_data).decode('utf-8')
            
            params = {
                'anilistInfo': 'true', 
                'cutBorders': 'true'  
            }
            
            payload = {
                'image': f'data:image/jpeg;base64,{image_base64}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_URL,
                    params=params,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 413:
                        logger.error("изображение слишком большое")
                        return None
                    elif response.status == 429:
                        logger.error("превышен лимит запросов")
                        return None
                    elif response.status != 200:
                        text = await response.text()
                        return None
                    
                    data = await response.json()
                    
                    if data.get('error'):
                        return None
                    
                    results = data.get('result', [])
                    
                    filtered_results = [
                        r for r in results 
                        if r.get('similarity', 0) > 0.87
                    ]
                    
                    return filtered_results if filtered_results else results[:3]
                    
        except Exception as e:
            logger.error(f"ошибка: {e}")
            
        return None
                
    except aiohttp.ClientError as e:
        logger.error(f"ошибка: {e}")
        return None
    except Exception as e:
        logger.error(f"ошибка: {e}")
        return None


async def get_anime_info(anilist_id: int):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{ANILIST_URL}/{anilist_id}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status != 200:
                    return None
                    
                return await response.json()
                
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None