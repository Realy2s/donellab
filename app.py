# -*- coding: utf-8 -*-
"""Matematik cozucu + var olan donel cisim, 3B STL, Braille arayuzu."""
import io
import re
import zipfile
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import sympy as sp
import cozum as c
from gemini_servisi import soru_coz
from matematik_motoru import dogrula, stl_uygun_mu, ifade

st.set_page_config(page_title="Matematik Çözücü ve Dönel Cisim STL", layout="wide")
st.title("Matematik Çözücü + Dönel Cisim STL")
st.caption("Fotoğraf veya metinle matematik • Gemini • SymPy kontrolü • 3B STL / Braille")

for k,v in {"f_in":"x", "a_in":"0", "b_in":"3", "tur":"",
            "cozum_sonucu":None, "dogrulama":None, "model_adi":"",
            "kuyruk":[], "kuyruk_sonuclari":[], "soru_metni":""}.items():
    st.session_state.setdefault(k,v)


def api_key_oku():
    try:
        return st.secrets.get('GEMINI_API_KEY','')
    except Exception:
        return ''


def coz_ve_kaydet(metin='', resim=None, mime=None, tek=True):
    data, model = soru_coz(api_key_oku(), metin=metin, resim=resim, mime_type=mime)
    try:
        kontrol = dogrula(data)
    except Exception as e:
        kontrol = {'islem':'Yerel doğrulama', 'sonuc':'Bu ifadede uygulanamadı: '+str(e)}
    if tek:
        st.session_state.cozum_sonucu = data
        st.session_state.model_adi = model
        st.session_state.dogrulama = kontrol
        if stl_uygun_mu(data):
            st.session_state.f_in = str(data['solid_function']).replace('**','^')
            st.session_state.a_in = str(data['lower_bound'])
            st.session_state.b_in = str(data['upper_bound'])
            st.session_state.tur = 'donel_hacim'
    return {'data':data,'model':model,'kontrol':kontrol}


def yanit_goster(sonuc):
    data = sonuc['data']
    st.markdown('**Anlaşılan soru:** ' + str(data.get('normalized_question') or '—'))
    st.markdown(str(data.get('explanation') or 'Çözüm alınamadı.'))
    if data.get('exact_answer'):
        st.success('**Sonuç:** '+str(data['exact_answer']))
    if sonuc.get('kontrol'):
        v=sonuc['kontrol']
        st.info(f"SymPy kontrolü — {v['islem']}: {v['sonuc']}")
    elif data.get('expression'):
        st.caption('Bu soru için bağımsız sembolik sonuç otomatik doğrulanamadı; yapay zekâ cevabını ayrıca kontrol edin.')
    st.caption('Yanıt modeli: '+sonuc['model'])
    if data.get('question_type') == 'solid_of_revolution' and not stl_uygun_mu(data):
        st.warning('Bu dönel cisim sorusu tek fonksiyonun x ekseni etrafında dönmesi biçiminde değil; otomatik STL aktarılmadı.')


with st.sidebar:
    st.header('📷 Matematik sorusu')
    st.text_area('Soruyu yaz', key='soru_metni', height=135,
                 placeholder='f(x)=x^2-4x+5, x>=2 iken tersini bulunuz.')
    gorsel = st.file_uploader('Fotoğraf seç',type=['jpg','jpeg','png','webp'],key='gorsel')
    kamera = st.camera_input('Kameradan çek',key='kamera_gorsel')
    if st.button('Soruyu çöz', type='primary', use_container_width=True):
        dosya = kamera if kamera is not None else gorsel
        try:
            with st.spinner('Soru çözümleniyor...'):
                coz_ve_kaydet(st.session_state.soru_metni,
                              dosya.getvalue() if dosya else None,
                              getattr(dosya,'type',None) if dosya else None)
        except Exception as e:
            st.error('Gemini isteği başarısız: '+str(e))

    st.divider()
    st.subheader('📚 Çoklu sorular (tek tek)')
    dosyalar = st.file_uploader('Soru resimleri',type=['jpg','jpeg','png','webp'],
                               accept_multiple_files=True,key='toplu_gorseller')
    if st.button('Seçilenleri kuyruğa ekle', use_container_width=True):
        kalan = max(0,308-len(st.session_state.kuyruk))
        eklenen=0
        for f in dosyalar[:kalan]:
            if f.size > 8*1024*1024:
                st.warning(f.name+' 8 MB üzeri; atlandı.')
                continue
            st.session_state.kuyruk.append((f.name,f.getvalue(),f.type))
            eklenen += 1
        st.success(f'{eklenen} fotoğraf kuyruğa eklendi.')
    st.caption(f"Bekleyen: {len(st.session_state.kuyruk)} • Tamamlanan: {len(st.session_state.kuyruk_sonuclari)}")
    if st.button('Sıradaki 1 soruyu çöz', use_container_width=True):
        if not st.session_state.kuyruk: st.info('Kuyruk boş.')
        else:
            name,bts,mime = st.session_state.kuyruk[0]
            try:
                with st.spinner(name+' işleniyor...'):
                    result=coz_ve_kaydet(resim=bts,mime=mime,tek=False)
                st.session_state.kuyruk.pop(0)
                st.session_state.kuyruk_sonuclari.append((name,result))
                st.success(name+' tamamlandı.')
            except Exception as e:
                st.error(name+' işlenemedi, kuyrukta kaldı: '+str(e))
    if st.button('Sıradaki en fazla 3 soruyu sırayla çöz',use_container_width=True):
        for _ in range(min(3,len(st.session_state.kuyruk))):
            name,bts,mime=st.session_state.kuyruk[0]
            try:
                with st.spinner(name+' işleniyor...'):
                    result=coz_ve_kaydet(resim=bts,mime=mime,tek=False)
                st.session_state.kuyruk.pop(0)
                st.session_state.kuyruk_sonuclari.append((name,result))
            except Exception as e:
                st.error(name+' hata verdi; kalan sıra korunuyor: '+str(e))
                break
    if st.button('Kuyruğu temizle',use_container_width=True):
        st.session_state.kuyruk=[]
        st.session_state.kuyruk_sonuclari=[]

    st.divider()
    st.subheader('⚙️ Dönel cisim ayarları')
    st.text_input('f(x)',key='f_in',help='Örnek: x^2+1, sqrt(x), sin(x)')
    k1,k2=st.columns(2)
    k1.text_input('a',key='a_in')
    k2.text_input('b',key='b_in')
    n_disk=st.number_input('Disk sayısı',1,60,6)
    birim_mm=st.number_input('1 birim kaç mm (0=otomatik)',0.0,1000.0,10.0)
    sigdir_mm=st.number_input('Sığdırma boyutu (mm)',20,250,80)

sekme1, sekme2 = st.tabs(['🧠 Genel matematik çözümleri','🧊 Dönel cisim & STL'])
with sekme1:
    if st.session_state.cozum_sonucu is not None:
        yanit_goster({'data':st.session_state.cozum_sonucu,
                      'model':st.session_state.model_adi,
                      'kontrol':st.session_state.dogrulama})
    else:
        st.info('Soldan soru yazın veya fotoğraf yükleyip Soruyu çöz düğmesine basın.')
    if st.session_state.kuyruk_sonuclari:
        st.subheader('Toplu soru sonuçları')
        for i,(name,result) in enumerate(st.session_state.kuyruk_sonuclari):
            with st.expander(f'{i+1}. {name}'):
                yanit_goster(result)

    with st.expander('🔧 Gemini olmadan SymPy ile yerel hesaplama'):
        st.caption('Bu bölüm API istemez. Açık matematik ifadelerini hesaplar.')
        tur=st.selectbox('İşlem', ['evaluate','solve','derivative','factor','simplify','integral','volume'],
                         format_func=lambda v:{'evaluate':'Fonksiyon değeri','solve':'Denklem çöz',
                             'derivative':'Türev','factor':'Çarpanlara ayır','simplify':'Sadeleştir',
                             'integral':'İntegral','volume':'Dönel cisim hacmi'}[v])
        expr=st.text_input('İfade (2*x kullan)',value='x^2-5*x+6',key='yerel_ifade')
        at=st.text_input('x değeri (fonksiyon değeri için)',value='2',key='yerel_at')
        alt,ust=st.columns(2)
        aa=alt.text_input('Alt sınır (varsa)',key='yerel_a')
        bb=ust.text_input('Üst sınır (varsa)',key='yerel_b')
        if st.button('Yerel olarak hesapla'):
            try:
                v=dogrula({'sympy_task':tur,'expression':expr,'variable':'x',
                           'at':at,'lower_bound':aa,'upper_bound':bb})
                if v: st.success(v['islem']+': '+v['sonuc'])
                else: st.info('Bu işlem için yeterli bilgi yok.')
            except Exception as e:
                st.error('İfade işlenemedi: '+str(e))

with sekme2:
    st.divider()
    st.subheader("Dönel cisim hesabı ve 3B model")
    st.caption("Aşağıdaki bölüm mevcut cozum.py hesaplama ve STL işlevlerini kullanır.")

    try:
        s = c.hesapla(
            st.session_state.f_in,
            st.session_state.a_in,
            st.session_state.b_in,
            int(n_disk),
        )
        olcek, kucultuldu = c.olcek_bul(s, birim_mm, sigdir_mm)
    except Exception as hata:
        st.error(f"Dönel cisim hesaplanamadı: {hata}")
        st.stop()

    V = float(s["hacim_say"])
    V_mL = V * olcek**3 / 1000
    integral_sorusu = st.session_state.tur == "integral"


    def yaz(sem, sayi):
        return (f"{sp.pretty(sem, use_unicode=True)} ≈ " if sem is not None else "") + f"{sayi:.4f}"


    if integral_sorusu:
        st.success(f"**Dönel cisim sorusu:** ∫ f(x) dx = {yaz(s['alan_sem'], s['alan_say'])} birim²")
        st.caption(f"Eğri x-ekseni etrafında dönerse V = {yaz(s['hacim_sem'], V)} birim³")
    else:
        st.success(f"**Dönel cisim hacmi:** V = {yaz(s['hacim_sem'], V)} birim³")
        st.caption(f"Eğri altındaki alan ∫ f(x) dx = {yaz(s['alan_sem'], s['alan_say'])}")

    if s.get("ters_turev") is not None:
        st.caption(f"Ters türev: F(x) = {s['ters_turev']} → F(b) − F(a)")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Hacim (sayısal)", f"{V:.4f}")
    if abs(V) > 1e-12:
        hata_yuzdesi = abs(s["disk_toplam"] - V) / abs(V) * 100
        hata_metni = f"hata %{hata_yuzdesi:.2f}"
    else:
        hata_metni = "hacim sıfır"
    m2.metric(f"{s['n']} disk toplamı", f"{s['disk_toplam']:.4f}", hata_metni, delta_color="off")
    m3.metric("Ölçek", f"1 birim = {olcek:.2f} mm")
    m4.metric("Su testi (dolu kap)", f"{V_mL:.1f} mL")
    if kucultuldu:
        st.caption("Model 250 mm baskı alanına sığsın diye otomatik küçültüldü.")

    sol, sag = st.columns(2)
    with sol:
        st.subheader("3B model")
        mod = st.radio("Görünüm", ["Düz cisim", "Diskler"], horizontal=True)
        ucgenler = c.govde_ucgenleri(s, 1) if mod == "Düz cisim" else c.disk_ucgenleri(s, 1, s["dh"] * 0.12)
        if ucgenler:
            P = np.asarray([v for ucgen in ucgenler for v in ucgen], dtype=float)
            I = np.arange(len(P)).reshape(-1, 3)
            fig3 = go.Figure(go.Mesh3d(
                x=P[:, 0], y=P[:, 1], z=P[:, 2],
                i=I[:, 0], j=I[:, 1], k=I[:, 2],
                color="#3b82f6", flatshading=False, opacity=1,
            ))
            fig3.add_trace(go.Scatter3d(
                x=[s["a"], s["b"]], y=[0, 0], z=[0, 0],
                mode="lines", line=dict(color="orange", width=6), name="eksen",
            ))
            fig3.update_layout(scene=dict(aspectmode="data"), margin=dict(l=0, r=0, t=0, b=0), height=420)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("3B model için üçgen oluşturulamadı.")

    with sag:
        st.subheader("2B grafik")
        goster = st.checkbox("Disk kesitlerini göster", True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=s["xs"], y=s["r"], name="f(x)", line=dict(color="#2563eb", width=3)))
        fig2.add_trace(go.Scatter(
            x=s["xs"], y=-s["r"], name="−f(x)", line=dict(color="#2563eb", dash="dash"),
            fill="tonexty", fillcolor="rgba(59,130,246,0.12)",
        ))
        if goster:
            for k, rr in enumerate(s["disk_r"]):
                x0 = s["a"] + k * s["dh"]
                fig2.add_shape(type="rect", x0=x0, x1=x0 + s["dh"], y0=-rr, y1=rr,
                               line=dict(color="#6366f1"), fillcolor="rgba(99,102,241,0.12)")
        fig2.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="x", yaxis_title="y")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Braille etiket")
    for satir in c.etiket_satirlari(s, olcek):
        st.markdown(
            f"<span style='font-size:1.6rem;letter-spacing:.12em'>{c.braille_unicode(satir)}</span> &nbsp; `{satir}`",
            unsafe_allow_html=True,
        )

    dosyalar = c.zip_icerigi(s, olcek)
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
        for ad, veri in dosyalar.items():
            z.writestr(ad, veri)
        z.writestr(
            "OKU.txt",
            f"f(x)={s['f_metin']}, [{s['a']:g}, {s['b']:g}]\n"
            f"V={V:.4f} birim3\nOlcek: 1 birim = {olcek:.3f} mm\n"
            f"Beklenen su hacmi: {V_mL:.1f} mL\nSTL birimi mm.",
        )
    ad = re.sub(r"[^A-Za-z0-9]+", "_", f"{s['f_metin']}_{s['a']:g}_{s['b']:g}")[:40]
    st.download_button(
        "⬇ STL dosyalarını indir (.zip)", tampon.getvalue(),
        file_name=f"donel_{ad}.zip", mime="application/zip", type="primary",
    )
    st.caption(
        "ZIP: donel_cisim.stl (düz cisim), diskler.stl, "
        "etiket_eksen.stl (Braille + kabartma eksen), grafik_2d.stl (dokunsal grafik plakası)."
    )
