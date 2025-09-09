# utils.py (To'liq, yakuniy versiya)

import os
import logging
import yt_dlp
import requests

# Jurnallashni (logging) sozlash
logger = logging.getLogger(__name__)

# --- Railway.app uchun maxsus sozlama ---
# COOKIE_DATA nomli o'zgaruvchidan ma'lumotni o'qib, cookies.txt faylini yaratamiz.
COOKIE_FILE = 'cookies.txt'
cookie_data_from_env = os.getenv('COOKIE_DATA')

if cookie_data_from_env:
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        f.write(cookie_data_from_env)
    logger.info(f"'{COOKIE_FILE}' fayli server o'zgaruvchisidan muvaffaqiyatli yaratildi.")
else:
    logger.warning(f"Serverda 'COOKIE_DATA' o'zgaruvchisi topilmadi. Ayrim saytlarda yuklash ishlamasligi mumkin.")

# --- Asosiy Funksiyalar ---

def download_media(url: str, is_audio: bool, download_dir: str, max_size: int = None):
    """
    Berilgan URL manzildan yt-dlp yordamida media yuklaydi.
    """
    os.makedirs(download_dir, exist_ok=True)
    output_template = os.path.join(download_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'logger': logger,
        'outtmpl': output_template,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE
        logger.info(f"'{COOKIE_FILE}' fayli yuklash uchun ishlatilmoqda.")

    if max_size:
        ydl_opts['max_filesize'] = max_size

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
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            if not info_dict:
                raise Exception("Bu havola bo'yicha ma'lumot topilmadi.")

            video_id = info_dict.get('id')
            if not video_id:
                raise Exception("Media ID'sini aniqlab bo'lmadi.")

            logger.info(f"Yuklanmoqda: media ID '{video_id}' manbadan: {url}")
            ydl.download([url])

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
        if "File is larger than the maximum" in str(e):
            raise Exception(f"Fayl hajmi ruxsat etilgan limitdan katta.")
        raise Exception("Bu havoladan yuklab bo'lmadi.")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik yuz berdi: {e}")
        raise e


def upload_to_gofile(file_path):
    """
    Berilgan faylni GoFile.io servisiga yuklaydi va havolasini qaytaradi.
    """
    try:
        # 1. Yuklash uchun eng yaxshi serverni topamiz
        server_response = requests.get('https://api.gofile.io/getServer', timeout=10)
        server_response.raise_for_status()
        server = server_response.json()['data']['server']
        upload_url = f"https://{server}.gofile.io/uploadFile"

        logger.info(f"GoFile serveri topildi: {server}. Fayl yuklanmoqda...")

        # 2. Faylni serverga yuklaymiz
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(upload_url, files=files, timeout=300) # 5 daqiqa timeout
            response.raise_for_status()
        
        upload_data = response.json()

        if upload_data.get("status") == "ok":
            download_link = upload_data["data"]["downloadPage"]
            logger.info(f"Fayl GoFile.io ga muvaffaqiyatli yuklandi: {download_link}")
            return download_link
        else:
            logger.error(f"GoFile.io dan xatolik keldi: {upload_data}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"GoFile.io ga yuklashda tarmoq xatoligi: {e}")
        return None
    except Exception as e:
        logger.error(f"GoFile.io ga yuklashda kutilmagan xatolik: {e}")
        return None
