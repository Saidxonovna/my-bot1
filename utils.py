# utils.py faylidagi upload_to_gofile funksiyasini shu bilan almashtiring

def upload_to_gofile(file_path):
    """
    Berilgan faylni GoFile.io servisiga yuklaydi va havolasini qaytaradi.
    Endi API Token bilan ishlaydi.
    """
    gofile_token = os.getenv('GOFILE_TOKEN')
    if not gofile_token:
        logger.warning("Railway'da GOFILE_TOKEN topilmadi. Anonim rejimda yuklashga harakat qilinadi.")

    try:
        # 1. Yuklash uchun eng yaxshi serverni topamiz
        server_response = requests.get('https://api.gofile.io/getServer', timeout=15)
        server_response.raise_for_status()
        server = server_response.json()['data']['server']
        upload_url = f"https://{server}.gofile.io/uploadFile"

        logger.info(f"GoFile serveri topildi: {server}. Fayl yuklanmoqda...")
        
        # 2. Faylni va tokenni serverga yuboramiz
        with open(file_path, 'rb') as f:
            files = {'file': f}
            # Agar token mavjud bo'lsa, uni ham so'rovga qo'shamiz
            data = {'token': gofile_token} if gofile_token else {}
            
            response = requests.post(upload_url, files=files, data=data, timeout=300)
            response.raise_for_status()
        
        upload_data = response.json()

        if upload_data.get("status") == "ok":
            download_link = upload_data["data"]["downloadPage"]
            logger.info(f"Fayl GoFile.io ga muvaffaqiyatli yuklandi: {download_link}")
            return download_link
        else:
            # Agar tokendan xatolik bo'lsa, logda ko'rinadi
            logger.error(f"GoFile.io dan xatolik keldi: {upload_data.get('data', {}).get('error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"GoFile.io ga yuklashda tarmoq xatoligi: {e}")
        return None
    except Exception as e:
        logger.error(f"GoFile.io ga yuklashda kutilmagan xatolik: {e}")
        return None
