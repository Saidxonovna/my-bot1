# utils.py

import os
import logging
import yt_dlp

# Jurnallashni (logging) sozlash
logger = logging.getLogger(__name__)

# --- Railway.app uchun maxsus sozlama ---
# COOKIE_DATA nomli o'zgaruvchidan ma'lumotni o'qib, cookies.txt faylini yaratamiz.
# Bu bot har safar qayta ishga tushganda bajariladi.

COOKIE_FILE = 'cookies.txt'
cookie_data_from_env = os.getenv('COOKIE_DATA')

if cookie_data_from_env:
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        f.write(cookie_data_from_env)
    logger.info(f"'{COOKIE_FILE}' fayli server o'zgaruvchisidan muvaffaqiyatli yaratildi.")
else:
    logger.warning(f"Serverda 'COOKIE_DATA' o'zgaruvchisi topilmadi. Ayrim saytlarda yuklash ishlamasligi mumkin.")

# --- Asosiy Funksiya ---

def download_media(url: str, is_audio: bool, download_dir: str, max_size: int = None):
    """
    Berilgan URL manzildan yt-dlp yordamida media yuklaydi.

    Args:
        url (str): Yuklab olinadigan media havolasi.
        is_audio (bool): Faqat audio yuklash kerak bo'lsa True (mp3 formatida).
        download_dir (str): Yuklangan faylni saqlash uchun papka.
        max_size (int, optional): Baytlarda ruxsat etilgan maksimal fayl hajmi. Standart None.

    Returns:
        str: Yuklangan faylning to'liq yo'li (path).

    Raises:
        Exception: Agar yuklashda xatolik yuz bersa yoki fayl hajmi cheklovdan oshsa.
    """
    # Yuklash uchun papka mavjudligini tekshirish va yaratish
    os.makedirs(download_dir, exist_ok=True)

    # Yuklanadigan fayl uchun nom andozasi
    output_template = os.path.join(download_dir, '%(id)s.%(ext)s')

    # yt-dlp uchun asosiy sozlamalar
    ydl_opts = {
        'logger': logger,
        'outtmpl': output_template,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    # Agar cookies.txt fayli mavjud bo'lsa (yuqorida yaratdik), uni sozlamalarga qo'shamiz
    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE
        logger.info(f"'{COOKIE_FILE}' fayli yuklash uchun ishlatilmoqda.")

    # Agar fayl hajmi bo'yicha cheklov berilgan bo'lsa
    if max_size:
        ydl_opts['max_filesize'] = max_size

    # Yuklash turiga qarab formatni sozlash
    if is_audio:
        # Audio yuklash uchun (MP3 formatida)
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # Video yuklash uchun (MP4 formatida)
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferredformat': 'mp4',
            }],
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Avval ma'lumotni yuklamasdan olamiz
            info_dict = ydl.extract_info(url, download=False)

            if not info_dict:
                raise Exception("Bu havola bo'yicha ma'lumot topilmadi. Iltimos, havolani tekshiring.")

            video_id = info_dict.get('id')
            if not video_id:
                raise Exception("Media ID'sini aniqlab bo'lmadi.")

            logger.info(f"Yuklanmoqda: media ID '{video_id}' manbadan: {url}")
            
            # 2. Ma'lumot olingandan so'ng faylni yuklaymiz
            ydl.download([url])

            # 3. Yuklangan faylning to'liq yo'lini aniqlaymiz
            # Ba'zida format o'zgargani uchun kengaytmani dinamik topish kerak
            expected_ext = 'mp3' if is_audio else 'mp4'
            file_path = os.path.join(download_dir, f"{video_id}.{expected_ext}")

            if not os.path.exists(file_path):
                found_files = [f for f in os.listdir(download_dir) if f.startswith(video_id)]
                if found_files:
                    file_path = os.path.join(download_dir, found_files[0])
                    logger.info(f"Fayl boshqa kengaytma bilan topildi: {file_path}")
                else:
                    raise Exception(f"Yuklangan fayl topilmadi: '{video_id}'")

            logger.info(f"Muvaffaqiyatli yuklandi: {file_path}")
            return file_path

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp yuklashda xatolik: {e}")
        # Fayl hajmi bo'yicha xatolikni aniqroq ko'rsatish
        if "File is larger than the maximum" in str(e):
            raise Exception(f"Fayl hajmi ruxsat etilgan limitdan katta.")
        raise Exception("Bu havoladan yuklab bo'lmadi. Iltimos, URL manzilini tekshiring.")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik yuz berdi: {e}")
        raise e
