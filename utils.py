# utils.py faylining oxiriga qo'shing

import requests

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
