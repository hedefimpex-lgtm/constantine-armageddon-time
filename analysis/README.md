# İstanbul Kıyamet Vakti kurulumu

Resmî [indirme sayfasında](https://www.istanbuloyun.com/download.aspx) tek parça kurulum `istanbulkur6_0.exe` ve indirme yardımcısı `IKVDownloader.exe` ayrı dosyalar olarak sunulur. [İnceleme sonuçları](results.json) REA 6.8.0 ile elde edilmiştir.

| Örnek | İncelenen veri | Bulgular |
| --- | --- | --- |
| Tek parça kurulum | Başlangıçtaki 8 MiB içinde PE başlığı ve disk üzerindeki bölümlerin tamamı | 32 bit x86, sekiz bölüm, 329.728 bayt PE görüntüsü, beş farklı Windows DLL’sinden 96 içe aktarım girdisi |
| İndirme yardımcısı | 2.078.104 baytlık dosyanın tamamı ve içindeki PE görüntüsü | 32 bit x86, altı bölüm, on bir DLL ve 481 içe aktarım girdisi |

Yayımcının sunucusu kısmi HTTP yanıtında kurulumun toplam uzunluğunu 1.685.549.760 bayt olarak bildirdi. İlk 8 MiB’nin SHA-256 değeri `b57a777198a0f81908b07467d4126ad3cad3639f1bc90d1b9234ee21c2769f23`. Yardımcının tam dosya SHA-256 değeri `1cef6e6fc5afef06dcf1de6ae0213aad45fb55a198a42013bf5b558cef000510`. [Başlık ve yardımcı incelemesi](https://github.com/hedefimpex-lgtm/constantine-armageddon-time/actions/runs/42452423733)

Kurucunun içe aktarımları kurulum arayüzünü tarif eder. Motor, çizim ve ağ katmanlarını incelemek için paketteki oyun çalıştırılabilir dosyaları ayrı ele alınır.

## Tam kurulum ve oyun istemcisi

Resmî tek parça kurulumun tamamı indirildi. SHA-256 değeri `6fcfaaf85872fd7b88ca9eecef3d865e595ebc48a879fe9a6369812e440411c8`. Kurucu çalıştırılmadan innoextract ile 765 dosya çıkarıldı. Bunlar arasında 177 DDS dosyası, 77 OGG dosyası, 20 VSH ve 18 PSH dosyası var. [Tam inceleme çalışması](https://github.com/hedefimpex-lgtm/constantine-armageddon-time/actions/runs/42452635837)

| Çalıştırılabilir dosya | Doğrulanan özellikler |
| --- | --- |
| `app/istanbul.exe` | 32 bit x86 PE. İçe aktarımlar arasında Direct3D 9 (`d3d9.dll`, `d3dx9_31.dll`), DirectInput (`DINPUT8.dll`), DirectSound (`DSOUND.dll`) ve Winsock (`WS2_32.dll`) bulunur. |
| `app/launcher.exe` | 32 bit x86 PE. Windows arayüz ve ağ kitaplıklarını içe aktarır. |
| `app/launch_helper.exe` | 32 bit x86 PE. `KERNEL32.dll`, `USER32.dll` ve `SHELL32.dll` kitaplıklarını içe aktarır. |

Bu bulgular grafik, girdi, ses ve ağ bağımlılıklarını gösterir. Paket biçiminin, oturum açma adımlarının ve oyun sunucusunun mesajlarının belirlenmesi ayrı davranış incelemesi gerektirir. Mobil prototip kendi çizimlerini ve kendi oturum API’sini kullanır.

## Yerel dosyayı karşılaştırma

Python 3.11 veya üstü ve REA 6.8.0 bulunan makinede yerel kurulum dosyasına şu komutu uygulayın.

```sh
python3 scripts/inspect-installer.py /dosya/yolu/istanbulkur6_0.exe build/rea/yerel.json
```

Windows’ta yalnızca dosya kimliğini karşılaştırmak için:

```powershell
Get-FileHash -Algorithm SHA256 .\istanbulkur6_0.exe
```

WeTransfer kopyasının eşleşmesi için iki **tam dosya** özetinin aynı olması gerekir.
