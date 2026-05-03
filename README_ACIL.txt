ACIL DUZELTME PAKETI

Duzeltilenler:
1) Giriş ekranında takılı kalma problemi giderildi.
   Sebep: #loginScreen CSS display:flex!important olduğu için JS display:none etkisiz kalıyordu.
   Çözüm: login-hidden sınıfı eklendi.

2) Giriş ekranındaki NAKİT AKIŞ / YÖNETİM BİLGİ SİSTEMİ yazısı beyaz ve okunur yapıldı.

3) Giriş yap butonu tepkili hale getirildi:
   - basınca loading görünümü
   - active/click animasyonu
   - hatalı şifrede hızlı uyarı

4) Genel hız için login animasyon yükü azaltıldı, loader güvenli kapanır hale getirildi.

KURULUM:
- ZIP içeriğini sitenin ana dizinine çıkar.
- index.html ana dosyadır.
- assets klasörü ve data.json aynı dizinde kalmalıdır.

Giriş bilgileri mevcut sistemdeki gibidir:
Muhasebe / 3124411600
Etut / 3810431820
