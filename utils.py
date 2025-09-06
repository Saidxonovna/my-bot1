# utils.py

import os
import logging
import yt_dlp

# Jurnallashni (logging) sozlash
logger = logging.getLogger(__name__)

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
        Exception: Agar yuklashda xatolik yuz bersa.
    """
    # Yuklash papkasini yaratish (agar mavjud bo'lmasa)
    os.makedirs(download_dir, exist_ok=True)

    # Fayl nomini formatlash uchun shablon
    output_template = os.path.join(download_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'logger': logger,
        'outtmpl': output_template,
        'noplaylist': True,  # Faqat bitta videoni yuklash, playlistni emas
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    # Agar maksimal hajm belgilangan bo'lsa, uni qo'shamiz
    if max_size:
        ydl_opts['max_filesize'] = max_size

    if is_audio:
        # Audio (mp3) yuklash uchun sozlamalar
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',  # 192 kbps sifati
            }],
        })
    else:
        # Video (mp4) yuklash uchun sozlamalar
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
             'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Faylni yuklashdan oldin u haqida ma'lumot olamiz
            info_dict = ydl.extract_info(url, download=False)
            video_id = info_dict.get('id')
            
            if not video_id:
                raise Exception("Media haqida ma'lumot olib bo'lmadi.")
            
            # Mediani yuklash
            logger.info(f"Downloading media with id: {video_id} from {url}")
            ydl.download([url])
            
            # Yuklangan faylning nomini aniqlash
            # Audio yuklanganda kengaytma .mp3 bo'ladi
            expected_ext = 'mp3' if is_audio else info_dict.get('ext', 'mp4')
            file_path = os.path.join(download_dir, f"{video_id}.{expected_ext}")

            # Agar fayl kutilgan nom bilan topilmasa (format o'zgargan bo'lishi mumkin)
            if not os.path.exists(file_path):
                # Papkadagi fayllar orasidan to'g'ri ID bilan boshlanganini qidiramiz
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
        # Foydalanuvchiga tushunarliroq xabar berish
        if "File is larger than the maximum" in str(e):
             raise Exception(f"Fayl hajmi ruxsat etilgan {max_size // 1024 // 1024}MB dan katta.")
        raise Exception("Bu havoladan yuklab bo'lmadi. Iltimos, URL manzilini tekshiring.")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik yuz berdi: {e}")
        raise e

