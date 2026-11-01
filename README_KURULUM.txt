GELISMIS MATEMATIK COZUCU + DONEL CISIM STL
=========================================

GUNCELLENEN DOSYALAR
  app.py               -> Streamlit arayuzu / kuyruk
  gemini_servisi.py    -> Gemini Interactions API, 503 retry ve model fallback
  matematik_motoru.py  -> Guvenli ifade okuma ve SymPy kontrolu
  cozum.py             -> Donel cisim, 3B model, Braille ve STL fonksiyonlari
  requirements.txt     -> Pip kutuphaneleri

GITHUB / STREAMLIT CLOUD
1. Projenin mevcut app.py ve cozum.py dosyalarini yedekle.
2. ZIP'teki 5 dosyayi GitHub deponun ana klasorune yukle.
3. Streamlit Cloud uygulamanda Settings > Secrets alanina sunu yaz:
       GEMINI_API_KEY = "KENDI_GEMINI_API_ANAHTARIN"
   Bu anahtari GitHub deposuna, kod dosyasina veya ekran goruntusune KOYMA.
4. Uygulamayi yeniden deploy et. Main file path: app.py
5. 'Soruyu coz' ile tek soru; 'Coklu sorular' alanindan kuyruga
   ekleyip 1 veya 3 soruyu SIRAYLA isle.

WINDOWS BILGISAYAR
1. Python kurulu olmali.
2. ZIP'i ac, klasorde terminali baslat.
3. Komutlar:
       python -m pip install -r requirements.txt
       python -m streamlit run app.py
4. Yerel gelistirmede .streamlit/secrets.toml dosyasi olusturup
   GEMINI_API_KEY = "..." gir. Secrets dosyasini asla GitHub'a yukleme.

MODEL LISTESI (sira ile)
  gemini-3.8-flash -> gemini-3.6-flash -> gemini-3.5-flash-lite
Model bulunamiyorsa 404'te diger modele gecer.
429 veya 5xx hatalarinda 2 deneme ile kademeli bekler.
Erisim, plan ve kota her model icin farkli olabilir.

MATEMATIK DOGRLAMA
Gemini adim adim Turkce cozum yazar. SymPy, desteklenen acik
ifadelerin sonucunu ayrica hesaplar. Tum sozlu sorulari veya
ispatlari otomatik, kusursuz dogrulama iddiasi yoktur.

DONEL CISIM/STL SINIRI
Tek fonksiyon f(x), a,b sinirlari ve x ekseni etrafinda
360 derece donme icin 3B model/StL vardir. Iki fonksiyon veya
y ekseni etrafinda donen cisimlerde metinsel cozum verilebilir;
ancak otomatik STL aktarimi YAPILMAZ. Yanlis geometri olusturulmaz.

TOPLU SORU ISLEME
Kuyruk 308 resme kadar alir; tumunu tek anda API'ye GONDERMEZ.
Kuyruk st.session_state icinde tutulur, sayfa oturumu kapanirsa
kaybolabilir. Tek tek/sirayi bozmadan isleme icin dugmeleri kullan.
Tek dosya icin 8 MB siniri vardir. Coklu istekler ucretli olabilir;
kullanim limiti ve faturalandirmayi Google AI Studio'dan kontrol et.

SORUN GIDERME
- 503: gecici yogunluk; otomatik yeniden deneme ve fallback var.
- 404: model hesabin icin mevcut olmayabilir; fallback modeli dener.
- 401/403: API anahtari/erisim; Secrets kontrol et.
- 429: rate limit; kuyrugu daha seyrek isle, kotayi kontrol et.
- 'Interactions' bulunamiyor: google-genai kutuphanesini guncelle,
  requirements.txt dosyasini GitHub'a yukledikten sonra redeploy et.

DEGISIKLIK NOTU
Onceki 'google-genai' ile gelen generate_content cagrisinin yerini
Interactions API almistir. Pytesseract zorunlulugu kaldirildi; foto
Gemini'ye gonderilir. cozum.py ifadesi izinli AST matematik islemleri
ile parse edilir, dogrudan Python kodu calistirilmaz.
