# utils.py

import os
import logging
from yt_dlp import YoutubeDL

# Har bir fayl o'z loggeriga ega bo'lishi yaxshi amaliyotdir
logger = logging.getLogger(__name__)


def download_media(url: str, is_audio: bool, download_dir: str, max_size: int):
    """
    Videoni yoki audioni yuklab oladi va fayl yo'lini qaytaradi.
    FFmpeg ishlatmaslik uchun optimallashtirilgan.
    """
    os.makedirs(download_dir, exist_ok=True)

    # yt-dlp sozlamalari
    ydl_opts = {
        # Fayl nomini 60 belgidan oshirmaymiz, bu Telegram uchun qulay
        'outtmpl': os.path.join(download_dir, '%(title).60s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'socket_timeout': 20,
        'retries': 3,
        'fragment_retries': 3,
        'max_filesize': max_size,
    }

    if is_audio:
        # Audio yuklash uchun FFmpeg'siz sozlamalar
        ydl_opts.update({
            # Eng yaxshi audioni .m4a formatida yuklaymiz (Telegram qo'llab-quvvatlaydi)
            'format': 'bestaudio[ext=m4a]/bestaudio',
            # .mp3 ga o'girish uchun FFmpeg kerak, shuning uchun postprotsessorni o'chiramiz
            'postprocessors': [],
        })
    else:
        # Video yuklash uchun FFmpeg'siz sozlamalar
        # Odatda 720p gacha videolar audio bilan birga keladi
        ydl_opts['format'] = 'best[ext=mp4][height<=720]/best[ext=mp4]/best'

    with YoutubeDL(ydl_opts) as ydl:
        try:
            logger.info(f"Yuklash boshlandi: {url}, audio: {is_audio}")
            info = ydl.extract_info(url, download=True)

            # Yuklangan faylning aniq nomini olamiz
            filename = ydl.prepare_filename(info)

            # Agar fayl mavjud bo'lmasa (ba'zan kengaytma o'zgarishi mumkin)
            if not os.path.exists(filename):
                base, ext = os.path.splitext(filename)
                # Audio uchun .m4a, video uchun .mp4 kengaytmasini tekshiramiz
                expected_ext = '.m4a' if is_audio else '.mp4'
                if os.path.exists(base + expected_ext):
                    filename = base + expected_ext
                else:
                    # Agar hali ham topilmasa, xatolik beramiz
                    raise FileNotFoundError(
                        f"Yuklangan fayl topilmadi: {filename}")

            return filename

        except Exception as e:
            logger.error(f"Yuklashda xato ({url}): {e}")
            if 'File is larger than max-filesize' in str(e):
                raise ValueError("Fayl hajmi 50MB dan katta.")
            # Foydalanuvchiga tushunarliroq xabar berish
            raise Exception(
                "Havolani yuklab bo'lmadi. Keyinroq qayta urunib ko'ring.")
