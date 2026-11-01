# -*- coding: utf-8 -*-
"""Gemini Interactions API: sirasiyla isleme, gecici hata retry, model fallback."""
import base64
import json
import random
import re
import time

MODELLER = ('gemini-3.8-flash','gemini-3.6-flash','gemini-3.5-flash-lite')

PROMPT = '''Sen Turkce konusan dikkatli bir matematik ogretmenisin.
Ilkokuldan universiteye kadar matematik problemi cozmeye calis.
Fonksiyon, karmasik sozel problem, denklem, esitsizlik, trigonometri,
limit, turev, integral, geometri, olasilik ve donel cisimleri destekle.
Soruyu dogru yeniden ifade et, yeterli veri yoksa tahmin etme.
Cozumu adim adim Turkce yaz; sonucu kontrol et, emin degilsen belirt.
YALNIZCA asagidaki alanlari iceren gecerli JSON dondur (markdown kullanma):
{
  "question_type": "function|solid_of_revolution|other",
  "normalized_question": "soru metni",
  "explanation": "adim adim Turkce cozum",
  "exact_answer": "sonuc veya bos string",
  "sympy_task": "evaluate|solve|derivative|factor|simplify|integral|volume|none",
  "expression": "yalniz matematik ifadesi: x^2+1 veya x^2-4=0; diger durumda bos",
  "variable": "x",
  "at": "deger hesaplama ise ornek 4; diger durumda bos",
  "solid_function": "tek fonksiyonlu x ekseninde donen cisim ise f(x), degilse bos",
  "inner_expression": "iki egri arasinda ic fonksiyon varsa yaz, yoksa bos",
  "lower_bound": "varsa alt sinir; yoksa bos",
  "upper_bound": "varsa ust sinir; yoksa bos",
  "rotation_axis": "x|y|other|unknown"
}
Onemli: Diger matematik problemlerini asla donel cisim gibi isaretleme.
Iki egri veya y ekseni etrafinda donme durumunda tek fonksiyonlu STL uydurma.
SymPy alanlarinda 2*x kullan, 2x kullanma; ust icin ^, fonksiyon icin sqrt(x).
''' 


def _status(exc):
    status = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
    try: return int(status)
    except (ValueError,TypeError):
        m=re.search(r'\b(404|408|429|500|502|503|504)\b', str(exc))
        return int(m.group(1)) if m else None


def json_oku(text):
    s=(text or '').strip()
    if s.startswith('```'):
        s=re.sub(r'^```(?:json)?\s*|\s*```$', '', s, flags=re.I).strip()
    try: data=json.loads(s)
    except json.JSONDecodeError:
        m=re.search(r'\{.*\}', s, re.S)
        if m is None: raise ValueError('Gemini JSON olmayan cevap dondurdu.')
        data=json.loads(m.group(0))
    if not isinstance(data,dict) or not data.get('explanation'):
        raise ValueError('Gemini eksik cozum dondurdu.')
    return data


def soru_coz(api_key, metin='', resim=None, mime_type=None, max_attempts=2, sleep=time.sleep):
    """Bir soruya bir istek zinciri; asla paralel istek baslatmaz.

    resim: byte dizisi. Istege en fazla 8 MB resim kabul edilir.
    """
    if not api_key: raise ValueError('Streamlit Secrets icinde GEMINI_API_KEY yok.')
    if not metin.strip() and not resim: raise ValueError('Once soru yazin veya fotograf ekleyin.')
    if resim and len(resim)>8*1024*1024: raise ValueError('Resim 8 MB sinirini asiyor.')
    from google import genai
    client=genai.Client(api_key=api_key)
    input_data=[]
    input_data.append({'type':'text','text': PROMPT + '\nKULLANICININ SORUSU:\n' + (metin or '')})
    if resim:
        image_type=mime_type or 'image/jpeg'
        if image_type not in ('image/jpeg','image/png','image/webp'):
            raise ValueError('Yalniz JPG, PNG veya WEBP fotograflar kullanin.')
        input_data.append({'type':'image','data':base64.b64encode(resim).decode('ascii'),'mime_type':image_type})

    son_hata=None
    for model in MODELLER:
        for deneme in range(max_attempts):
            try:
                yanit=client.interactions.create(model=model, input=input_data)
                result=json_oku(yanit.output_text)
                return result,model
            except Exception as exc:
                code=_status(exc)
                son_hata=exc
                if code in (408,429,500,502,503,504):
                    if deneme < max_attempts-1:
                        sleep(min(12,2**deneme)+random.uniform(0,0.5))
                    continue
                if code==404:
                    # Model hesapta yoksa siradaki modeli dene.
                    break
                # 400/401/403 gibi istemci/izin hatalarinda israr etme.
                raise
    raise RuntimeError('Gemini modelleri yogun veya su anda erisilemiyor. '
                       'Islemi daha sonra tekrar deneyin. Son hata: '+str(son_hata))
