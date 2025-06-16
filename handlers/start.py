import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums import ContentType

from db.models.users import Users
from utils.anime_search import search_anime

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):

    user = message.from_user
    db_user = await Users.get_or_none(uid=user.id)
    
    if not db_user:
        await Users.create(
            uid=user.id,
            username=user.username
        )
        logger.info(f"Новый пользователь: {user.id} (@{user.username})")
    
    await message.answer(
        "👋 <b>Привет! Я AniSearch Bot</b>\n\n"
        
        "🔍 Отправь мне скриншот из аниме, и я попробую найти:\n"
        "• Название аниме\n"
        "• Номер эпизода\n"
        "• Точное время сцены\n\n"
        
        "📸 Просто отправь картинку и подожди немного!"
    )


@router.message(F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message):

    await Users.filter(uid=message.from_user.id).update(last_active=message.date)
    
    user = await Users.get(uid=message.from_user.id)
    if user.is_blocked:
        await message.answer("❌ Вы заблокированы в боте")
        return
    
    status_msg = await message.answer(
        "🔍 Ищу аниме по изображению..."
    )
    
    try:
        photo = message.photo[-2] if len(message.photo) > 1 else message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        
        if file.file_size and file.file_size > 20 * 1024 * 1024:
            await status_msg.edit_text(
                "❌ Изображение слишком большое.\n"
                "Попробуйте отправить изображение меньшего размера."
            )
            return
        
        file_bytes = await message.bot.download_file(file.file_path)
        results = await search_anime(file_bytes.read())
        
        if not results:
            await status_msg.edit_text(
                "😔 К сожалению, не удалось найти это аниме.\n"
                "Возможные причины:\n"
                "• Изображение слишком большое\n"
                "• Плохое качество кадра\n"
                "• Аниме отсутствует в базе\n\n"
                
                "Попробуйте отправить другой кадр!"
            )
            return
        
        best_match = results[0]
        similarity = round(best_match['similarity'] * 100, 2)
        
        anime_info = best_match.get('anilist', {})
        title = anime_info.get('title', {})
        
        anime_name = (
            title.get('native') or 
            title.get('romaji') or 
            title.get('english') or 
            'Неизвестное аниме'
        )
        
        episode = best_match.get('episode', '?')
        time_from = best_match.get('from', 0)
        time_to = best_match.get('to', 0)
        
        def seconds_to_time(seconds):
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"
        
        time_str = f"{seconds_to_time(time_from)} - {seconds_to_time(time_to)}"
        
        response_text = (
            f"✅ <b>Найдено!</b>\n\n"
            f"📺 <b>Аниме:</b> {anime_name}\n"
            f"📼 <b>Эпизод:</b> {episode}\n"
            f"⏱ <b>Время:</b> {time_str}\n"
            f"🎯 <b>Точность:</b> {similarity}%"
        )
        
        if anime_info.get('id'):
            response_text += f"\n\n🔗 <a href='https://anilist.co/anime/{anime_info['id']}'>Страница на AniList</a>"
        
        await status_msg.edit_text(response_text)
        
    except Exception as e:
        logger.error(f"Ошибка при поиске аниме: {e}")
        await status_msg.edit_text(
            "❌ Произошла ошибка при поиске.\n"
            "Попробуйте еще раз позже."
        )