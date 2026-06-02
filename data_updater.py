#!/usr/bin/env python3
"""
data_updater.py v2
==================
Yeni JSON formatını ({"data":[...]}) okur, CFO Dashboard için data.json üretir.

Kullanım:
  python data_updater.py                          # data.json → data_out.json
  python data_updater.py --input veri.json        # farklı dosya
  python data_updater.py --input veri.json --output data.json
"""

import json, argparse, os, sys
from datetime import datetime
from collections import defaultdict
import numpy as np

# ── MAPPING KURALLARI (Nakit İşlem Detayı → Rapor Mapping + Yönü) ────
MAPPING_RULES = {
    # GİRİŞLER
    'GELEN FATURA':                         ('FAALİYET NAKİT GİRİŞİ',                          'GİRİŞ'),
    'GELEN FATURA GRUP İÇİ':               ('FİRMA BAZLI GRUP İÇİ NAKİT GİRİŞİ',               'GİRİŞ'),
    'GELEN ÖDEME GRUP İÇİ':                ('FİRMA BAZLI GRUP İÇİ NAKİT GİRİŞİ',               'GİRİŞ'),
    'MÜŞTERİ TAHSİLATI':                   ('FAALİYET NAKİT GİRİŞİ',                            'GİRİŞ'),
    'GELEN ÇEK':                            ('FAALİYET NAKİT GİRİŞİ / ÇEK',                     'GİRİŞ'),
    'GELEN SENET':                          ('FAALİYET NAKİT GİRİŞİ / ÇEK',                     'GİRİŞ'),
    'FAİZ GELİRİ':                          ('FİNANSMAN NAKİT GİRİŞİ / FAİZ',                   'GİRİŞ'),
    'FAİZ GELİRİ STOPAJ VER.':             ('FİNANSMAN NAKİT ÇIKIŞI / FAİZ STOPAJI',            'ÇIKIŞ'),
    'ORTAKTAN GELEN PARA':                  ('FİNANSMAN NAKİT GİRİŞİ / ORTAK',                  'GİRİŞ'),
    'NAKİT YATIRMA':                        ('NAKİT AKTARIMI / RAPOR DIŞI',                      'NÖTR'),
    # ÇIKIŞLAR
    'SATICI ÖDEMESİ':                       ('FAALİYET NAKİT ÇIKIŞI',                            'ÇIKIŞ'),
    'GİDEN FATURA':                         ('FAALİYET NAKİT ÇIKIŞI',                            'ÇIKIŞ'),
    'GİDEN ÖDEME':                          ('FAALİYET NAKİT ÇIKIŞI',                            'ÇIKIŞ'),
    'GİDEN FATURA GRUP İÇİ':              ('FİRMA BAZLI GRUP İÇİ NAKİT ÇIKIŞI',               'ÇIKIŞ'),
    'MAAŞ ÖDEMESİ':                        ('FAALİYET NAKİT ÇIKIŞI / PERSONEL',                 'ÇIKIŞ'),
    'MAAŞ AVANSI':                          ('FAALİYET NAKİT ÇIKIŞI / PERSONEL AVANSI',          'ÇIKIŞ'),
    'PERSONEL İCRA ÖDEMESİ':              ('FAALİYET NAKİT ÇIKIŞI / PERSONEL İCRA',            'ÇIKIŞ'),
    'YILLIK İZİN ÖDEMESİ':               ('FAALİYET NAKİT ÇIKIŞI / PERSONEL',                  'ÇIKIŞ'),
    'BURS ÖDEMESİ':                        ('FAALİYET DIŞI NAKİT ÇIKIŞI / BURS',                'ÇIKIŞ'),
    'BANKA MASRAFI':                        ('FAALİYET NAKİT ÇIKIŞI / BANKA MASRAFI',            'ÇIKIŞ'),
    'TEMİNAT MEKTUBU KOMİSYONU':          ('FAALİYET NAKİT ÇIKIŞI / BANKA MASRAFI',            'ÇIKIŞ'),
    'TEMİNAT MEK. KOMİSYON':             ('FAALİYET NAKİT ÇIKIŞI / BANKA MASRAFI',             'ÇIKIŞ'),
    'HAVALE ÜCRETİ':                       ('FAALİYET NAKİT ÇIKIŞI / BANKA MASRAFI',            'ÇIKIŞ'),
    'BSMV ÖDEMESİ':                        ('FAALİYET NAKİT ÇIKIŞI / BANKA MASRAFI',            'ÇIKIŞ'),
    'İŞ AVANSI':                            ('FAALİYET NAKİT ÇIKIŞI / İŞ AVANSI',               'ÇIKIŞ'),
    'GİDEN ÖDEME KARŞILIKSIZ':            ('FAALİYET DIŞI NAKİT ÇIKIŞI / KARŞILIKSIZ AVANS',   'ÇIKIŞ'),
    'İŞ AVANSI (KARŞILIKSIZ)':            ('FAALİYET DIŞI NAKİT ÇIKIŞI / KARŞILIKSIZ AVANS',   'ÇIKIŞ'),
    'ÇEK ÖDEMESİ':                         ('FAALİYET NAKİT ÇIKIŞI / ÇEK ÖDEMESİ',              'ÇIKIŞ'),
    'GİDEN ÇEK':                            ('FAALİYET NAKİT ÇIKIŞI / ÇEK ÖDEMESİ',              'ÇIKIŞ'),
    'SENET ÖDEMESİ':                        ('FAALİYET NAKİT ÇIKIŞI / ÇEK ÖDEMESİ',              'ÇIKIŞ'),
    'VERGİ ÖDEMESİ':                        ('FAALİYET NAKİT ÇIKIŞI / RESMİ ÖDEME',              'ÇIKIŞ'),
    'SGK ÖDEMESİ':                          ('FAALİYET NAKİT ÇIKIŞI / SGK',                      'ÇIKIŞ'),
    'BES ÖDEMESİ':                          ('FAALİYET NAKİT ÇIKIŞI / BES',                      'ÇIKIŞ'),
    'KİRA ÖDEMESİ':                         ('FAALİYET NAKİT ÇIKIŞI / KİRA',                     'ÇIKIŞ'),
    'SİGORTA ÖDEMESİ':                     ('FAALİYET NAKİT ÇIKIŞI / SİGORTA',                  'ÇIKIŞ'),
    'MASRAF FİŞİ':                          ('FAALİYET NAKİT ÇIKIŞI / MASRAF',                   'ÇIKIŞ'),
    'KREDİ ÖDEMESİ':                        ('FİNANSMAN NAKİT ÇIKIŞI / LEASİNG',                 'ÇIKIŞ'),
    'KREDİ KARTI BORÇ ÖDEMESİ':           ('FİNANSMAN NAKİT ÇIKIŞI / KREDİ KARTI',             'ÇIKIŞ'),
    'FAİZ ÖDEMESİ':                         ('FİNANSMAN NAKİT ÇIKIŞI / FAİZ STOPAJI',            'ÇIKIŞ'),
    'ORTAĞA VERİLEN PARA':                  ('FİNANSMAN NAKİT ÇIKIŞI / ORTAK',                   'ÇIKIŞ'),
    'KAR PAYI ÖDEMESİ':                    ('FİNANSMAN NAKİT ÇIKIŞI / KAR PAYI',                'ÇIKIŞ'),
    'LEASING ÖDEMESİ':                     ('FİNANSMAN NAKİT ÇIKIŞI / LEASİNG',                 'ÇIKIŞ'),
    'YATIRIM HARCAMASI':                    ('YATIRIM NAKİT ÇIKIŞI',                              'ÇIKIŞ'),
    'ARSA/ARAZİ ALIŞI':                    ('YATIRIM NAKİT ÇIKIŞI / ARAZİ/ARSA ALIŞI',          'ÇIKIŞ'),
    # NÖTR / RAPOR DIŞI
    'HESAPLAR ARASI VİRMAN':              ('NAKİT AKTARIMI / RAPOR DIŞI',                        'NÖTR'),
    'BANKALAR ARASI VİRMAN':              ('NAKİT AKTARIMI / RAPOR DIŞI',                        'NÖTR'),
    'DÖVİZ ALIŞ/SATIŞ':                   ('NAKİT DÖNÜŞÜMÜ / RAPOR DIŞI',                       'NÖTR'),
    'BAKİYE DÜZELTME':                     ('NAKİT ETKİSİ YOK / TAHAKKUK',                       'NÖTR'),
    'GELEN FATURA':                         ('NAKİT ETKİSİ YOK / TAHAKKUK',                       'NÖTR'),  # override aşağıda
    'NAKİT ÇEKİMİ':                        ('NAKİT AKTARIMI / RAPOR DIŞI',                        'NÖTR'),
}
# Nakit İşlem Detayı → RM (override — önceki GELEN FATURA düzeltme)
MAPPING_RULES['GELEN FATURA'] = ('FAALİYET NAKİT GİRİŞİ', 'GİRİŞ')

RAPOR_DISI = {
    'NAKİT AKTARIMI / RAPOR DIŞI', 'NAKİT DÖNÜŞÜMÜ / RAPOR DIŞI',
    'NAKİT ETKİSİ YOK / TAHAKKUK', 'NAKİT DIŞI DÜZELTME', 'KONTROL'
}
ORTAKLAR = {
    'SEMRA AYRANCIOĞLU','OĞUZ AYRANCIOĞLU',
    'HACER AYRANCIOĞLU YETİŞ','OSMAN AYRANCIOĞLU','İHSAN AYRANCIOĞLU'
}

def clean(v):
    if v is None: return ''
    s = str(v).strip()
    return '' if s in ('None','nan','NaN','null') else s

def to_float(v):
    try: return float(str(v).replace(',','.'))
    except: return 0.0

def parse_date(v):
    s = clean(v)
    if not s: return ''
    for fmt in ('%d.%m.%Y','%Y-%m-%d','%d/%m/%Y'):
        try:
            from datetime import datetime as dt
            return dt.strptime(s, fmt).strftime('%Y-%m-%d')
        except: pass
    return s[:10]

def get_ay(tarih_str):
    if len(tarih_str) >= 7: return tarih_str[:7]
    return ''

ORTAKLAR_SET = {
    'SEMRA AYRANCIOĞLU','OĞUZ AYRANCIOĞLU',
    'HACER AYRANCIOĞLU YETİŞ','OSMAN AYRANCIOĞLU','İHSAN AYRANCIOĞLU'
}

def auto_map(det, tutar, alici=''):
    # Eğer alıcı ortak ise → finansman çıkışı (personel değil)
    if alici and alici.strip() in ORTAKLAR_SET and tutar < 0:
        return ('FİNANSMAN NAKİT ÇIKIŞI / ORTAK', 'ÇIKIŞ')
    key = det.strip().upper()
    if key in MAPPING_RULES:
        return MAPPING_RULES[key]
    if tutar > 0: return ('DİĞER NAKİT GİRİŞİ', 'GİRİŞ')
    if tutar < 0: return ('DİĞER NAKİT ÇIKIŞI', 'ÇIKIŞ')
    return ('NAKİT ETKİSİ YOK / TAHAKKUK', 'NÖTR')

def run(input_path, output_path):
    print(f"[{datetime.now():%H:%M:%S}] Okunuyor: {input_path}")
    with open(input_path, 'rb') as f:
        raw = f.read()
    # BOM varsa kaldır
    if raw[:3] == b'\xef\xbb\xbf': raw = raw[3:]
    src = json.loads(raw, strict=False)
    # Format: {"data":[...]} veya direkt liste
    rows = src['data'] if isinstance(src, dict) and 'data' in src else src
    print(f"[{datetime.now():%H:%M:%S}] {len(rows):,} kayıt yüklendi")

    # ── İŞLE ────────────────────────────────────────────────────────────
    detay = []
    for r in rows:
        tarih  = parse_date(r.get('Tarih',''))
        firma  = clean(r.get('İşlem Yapan Firma',''))
        banka  = clean(r.get('İşlem Yapan Banka',''))
        det    = clean(r.get('Nakit İşlem Detayı',''))
        alici  = clean(r.get('Alıcı Ünvanı',''))
        banka_adi = clean(r.get('Banka Adı',''))
        tutar  = to_float(r.get('Tutar', 0))
        doviz  = clean(r.get('Döviz Cinsi',''))
        dov_bak= to_float(r.get('Döviz Bakiyesi', 0))
        aciklama = clean(r.get('Açıklama',''))[:60]
        rm_orig = clean(r.get('Rapor Mapping',''))
        yon_orig = clean(r.get('Yönü',''))

        ay = get_ay(tarih)

        # Mapping karar
        if rm_orig and rm_orig not in ('KONTROL',):
            rm = rm_orig
            yon = yon_orig if yon_orig in ('GİRİŞ','ÇIKIŞ','NÖTR') else (
                'GİRİŞ' if tutar > 0 else 'ÇIKIŞ' if tutar < 0 else 'NÖTR')
            # Alıcı ortak ama RM personel ise → ortak çıkışına düzelt
            if alici and alici.strip() in ORTAKLAR_SET and 'PERSONEL' in rm and tutar < 0:
                rm = 'FİNANSMAN NAKİT ÇIKIŞI / ORTAK'
            kaynak = 'orijinal'
        else:
            rm, yon = auto_map(det, tutar, alici)
            kaynak = 'auto'

        detay.append({
            'tarih': tarih, 'firma': firma, 'banka': banka,
            'nakit_det': det, 'alici': alici, 'banka_adi': banka_adi,
            'tutar': tutar, 'doviz': doviz, 'dov_bak': dov_bak,
            'aciklama': aciklama, 'rm': rm, 'yon': yon,
            'ay': ay, 'kaynak': kaynak,
        })

    # ── HESAPLAMALAR ────────────────────────────────────────────────────
    df_aktif = [r for r in detay if r['rm'] not in RAPOR_DISI]
    months = sorted(set(r['ay'] for r in detay if r['ay']))
    firms  = sorted(set(r['firma'] for r in detay if r['firma']))
    son3   = months[-3:] if len(months) >= 3 else months

    # Aylık
    monthly = []
    for ay in months:
        sub = [r for r in df_aktif if r['ay']==ay]
        g = sum(r['tutar'] for r in sub if r['yon']=='GİRİŞ')
        c = sum(r['tutar'] for r in sub if r['yon']=='ÇIKIŞ')
        orig = sum(1 for r in sub if r['kaynak']=='orijinal')
        auto = sum(1 for r in sub if r['kaynak']=='auto')
        monthly.append({'ay':ay,'giris':round(g,2),'cikis':round(c,2),'net':round(g+c,2),'orig':orig,'auto':auto})

    # Firma
    firma_data = []
    for firma in firms:
        f = [r for r in df_aktif if r['firma']==firma]
        g = sum(r['tutar'] for r in f if r['yon']=='GİRİŞ')
        c = sum(r['tutar'] for r in f if r['yon']=='ÇIKIŞ')
        burn3 = abs(sum(r['tutar'] for r in f if r['ay'] in son3 and r['yon']=='ÇIKIŞ') / max(len(son3),1))
        cs = ms = 0
        for ay in months:
            n = sum(r['tutar'] for r in f if r['ay']==ay)
            if n < 0: cs += 1; ms = max(ms, cs)
            else: cs = 0
        fin_g = sum(r['tutar'] for r in f if 'FİNANSMAN NAKİT GİRİŞİ' in r['rm'])
        tot_g = sum(r['tutar'] for r in f if r['yon']=='GİRİŞ')
        fin_bag = round(fin_g/tot_g*100 if tot_g > 0 else 0, 1)
        son3_net = sum(r['tutar'] for r in f if r['ay'] in son3)
        firma_data.append({
            'firma': firma, 'net': round(g+c,2), 'toplam_giris': round(g,2),
            'toplam_cikis': round(c,2), 'avg_monthly_burn': round(burn3,2),
            'max_neg_streak': int(ms), 'finansman_bag_pct': fin_bag,
            'son3ay_net': round(son3_net,2), 'islem_sayi': len(f),
            'orig_pct': round(sum(1 for r in f if r['kaynak']=='orijinal')/max(len(f),1)*100,1),
            'ortak': firma in ORTAKLAR,
        })

    # RM kategorileri
    rm_map = defaultdict(lambda: {'sum':0,'count':0})
    for r in df_aktif:
        rm_map[r['rm']]['sum'] += r['tutar']
        rm_map[r['rm']]['count'] += 1
    rm_list = [{'rm':k,'toplam':round(v['sum'],2),'sayi':v['count']} for k,v in sorted(rm_map.items(), key=lambda x:x[1]['sum'])]

    top_c = sorted([(k,v['sum']) for k,v in rm_map.items() if v['sum']<0], key=lambda x:x[1])[:12]
    top_g = sorted([(k,v['sum']) for k,v in rm_map.items() if v['sum']>0], key=lambda x:-x[1])[:12]

    # Anormal (z-skor)
    tutarlar = [abs(r['tutar']) for r in df_aktif if r['tutar'] != 0]
    mean_t = float(np.mean(tutarlar)) if tutarlar else 0
    std_t  = float(np.std(tutarlar))  if tutarlar else 1
    thr = mean_t + 2.5 * std_t
    anormal = sorted([r for r in df_aktif if abs(r['tutar']) > thr],
                     key=lambda x: abs(x['tutar']), reverse=True)[:30]
    anormal_list = [{**r, 'zscore': round((abs(r['tutar'])-mean_t)/std_t,1)} for r in anormal]

    # Döviz
    doviz_risk = []
    for dv in ['EUR','USD','TL','VADELİ','TEMLİK']:
        sub = [r for r in df_aktif if r['doviz']==dv]
        if not sub: continue
        g2 = sum(r['tutar'] for r in sub if r['yon']=='GİRİŞ')
        c2 = sum(r['tutar'] for r in sub if r['yon']=='ÇIKIŞ')
        doviz_risk.append({'doviz':dv,'giris':round(g2,2),'cikis':round(c2,2),'net':round(g2+c2,2),'islem':len(sub)})

    # Günlük son 120
    gun_map = defaultdict(float)
    for r in df_aktif:
        if r['tarih']: gun_map[r['tarih']] += r['tutar']
    gunluk = [{'gun':k,'net':round(v,2)} for k,v in sorted(gun_map.items())[-120:]]

    # Grup network
    gf = defaultdict(lambda:{'veren':0,'alan':0,'islem':0})
    for r in [r for r in detay if 'ORTAK' in r['rm'] or 'GRUP' in r['rm']]:
        f = r['firma']
        if r['yon']=='ÇIKIŞ': gf[f]['veren'] += abs(r['tutar'])
        if r['yon']=='GİRİŞ': gf[f]['alan']  += r['tutar']
        gf[f]['islem'] += 1
    grup_network = [{'firma':k,'veren':round(v['veren'],2),'alan':round(v['alan'],2),
                     'net':round(v['alan']-v['veren'],2),'islem':v['islem']} for k,v in gf.items()]

    # Ortak analiz
    ortak_alan = defaultdict(float)
    for r in detay:
        if r['alici'] in ORTAKLAR and r['yon']=='ÇIKIŞ':
            ortak_alan[r['firma']] += r['tutar']
    tot_out = sum(v for v in ortak_alan.values())
    tot_in  = sum(r['tutar'] for r in detay if r['firma'] in ORTAKLAR and r['yon']=='GİRİŞ')
    ortak_analiz = {
        'ortaklar': list(ORTAKLAR),
        'firmadan_ortaga': [{'firma':k,'tutar':round(v,2)} for k,v in sorted(ortak_alan.items(),key=lambda x:x[1])[:20]],
        'toplam_ortaga_cikan': round(tot_out,2),
        'toplam_ortaktan_gelen': round(tot_in,2),
    }

    # KPI
    TG = sum(r['tutar'] for r in df_aktif if r['yon']=='GİRİŞ')
    TC = sum(r['tutar'] for r in df_aktif if r['yon']=='ÇIKIŞ')

    master = {
        'meta': {
            'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'total_rows': len(detay), 'aktif_rows': len(df_aktif),
            'orig_rows': sum(1 for r in detay if r['kaynak']=='orijinal'),
            'auto_rows': sum(1 for r in detay if r['kaynak']=='auto'),
            'months': months, 'firms': firms,
            'rm_cats': sorted(rm_map.keys()),
            'bankalar': sorted(set(r['banka'] for r in detay if r['banka'])),
            'nakit_detaylar': sorted(set(r['nakit_det'] for r in detay if r['nakit_det'])),
            'dovizler': sorted(set(r['doviz'] for r in detay if r['doviz'])),
            'threshold_anormal': round(thr,0), 'mean_islem': round(mean_t,0),
            'firma_tipleri': {f: ('ortak' if f in ORTAKLAR else 'ticari') for f in firms},
        },
        'kpi': {'total_giris':round(TG,2),'total_cikis':round(TC,2),'net':round(TG+TC,2),
                'n_firma':len(firms),'n_islem':len(df_aktif),'n_islem_ham':len(detay)},
        'monthly': monthly,
        'firma': sorted(firma_data, key=lambda x:x['net']),
        'rm': rm_list,
        'top_cikis': [{'label':k,'val':round(v,2)} for k,v in top_c],
        'top_giris': [{'label':k,'val':round(v,2)} for k,v in top_g],
        'detay': detay,
        'anormal': anormal_list,
        'doviz_risk': doviz_risk,
        'gunluk': gunluk,
        'grup_network': grup_network,
        'ortak_analiz': ortak_analiz,
    }

    with open(output_path,'w',encoding='utf-8') as f:
        json.dump(master, f, ensure_ascii=False, separators=(',',':'))

    size = os.path.getsize(output_path)/1024/1024
    print(f"[{datetime.now():%H:%M:%S}] ✓ {output_path} ({size:.1f} MB)")
    print(f"  Ham: {len(detay):,}  Aktif: {len(df_aktif):,}  Orijinal RM: {master['meta']['orig_rows']:,}  Auto: {master['meta']['auto_rows']:,}")
    print(f"  Giriş: {TG:,.0f}  Çıkış: {TC:,.0f}  Net: {TG+TC:,.0f}")

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='JSON veri → CFO Dashboard data.json')
    ap.add_argument('--input',  default='data.json',     help='Kaynak JSON dosyası')
    ap.add_argument('--output', default='data_out.json', help='Çıktı dosyası')
    args = ap.parse_args()
    if not os.path.exists(args.input):
        print(f"HATA: {args.input} bulunamadı"); sys.exit(1)
    run(args.input, args.output)
