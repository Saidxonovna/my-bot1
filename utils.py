# utils.py

import os
import logging
import yt_dlp

logger = logging.getLogger(__name__)

# COOKIE FAYLNING NOMI
COOKIE_FILE = 'cookies.txt'

def download_media(url: str, is_audio: bool, download_dir: str, max_size: int = None):
    os.makedirs(download_dir, exist_ok=True)

    output_template = os.path.join(download_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'logger': logger,
        'outtmpl': output_template,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    # --- 1. COOKIE FAYLNI QO'SHISH ---
    # Agar cookies.txt fayli mavjud bo'lsa, uni sozlamalarga qo'shamiz
    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE
        logger.info(f"'{COOKIE_FILE}' fayli topildi va ishlatilmoqda.")
    else:
        logger.warning(f"'{COOKIE_FILE}' fayli topilmadi. Ba'zi saytlarda yuklash ishlamasligi mumkin.")

    if max_size:
        ydl_opts['max_filesize'] = max_size
    
    # --- 2. FORMATNI SODDALASHTIRISH ---
    # Bu ko'proq saytlarda ishlash imkonini beradi
    if is_audio:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best', # Eng yaxshi video va audioni birlashtirish
             'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            
            if not info_dict:
                raise Exception("Bu havola bo'yicha ma'lumot topilmadi. Iltimos, havolani tekshiring.")
            
            video_id = info_dict.get('id')
            
            if not video_id:
                raise Exception("Media ID sini aniqlab bo'lmadi.")
            
            logger.info(f"Downloading media with id: {video_id} from {url}")
            ydl.download([url])
            
            expected_ext = 'mp3' if is_audio else info_dict.get('ext', 'mp4')
            file_path = os.path.join(download_dir, f"{video_id}.{expected_ext}")

            if not os.path.exists(file_path):
                found_files = [f for f in os.listdir(download_dir) if f.startswith(video_id)]
                if found_files:
                    file_path = os.path.join(download_dir, found_files[0])
                    logger.info(f"File found with a different extension: {file_path}")
                else:
                    raise Exception(f"Yuklangan fayl topilmadi: {video_id}")

            logger.info(f"Muvaffaqiyatli yuklandi: {file_path}")
            return file_path

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp yuklashda xatolik: {e}")
        raise Exception("Bu havoladan yuklab bo'lmadi. Iltimos, URL manzilini tekshiring.")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik yuz berdi: {e}")
        raise e
