# Orijinal pakette bölge ve karakter verileri

İncelenen örnek yayımcının `istanbulkur6_0.exe` kurulumudur. Tam dosyanın SHA-256 değeri `6fcfaaf85872fd7b88ca9eecef3d865e595ebc48a879fe9a6369812e440411c8`. Kurulum çalıştırılmadan açıldı. [Dosya dizini ve içerik taraması](https://github.com/hedefimpex-lgtm/constantine-armageddon-time/actions/runs/42502992966)

| Dosya veya grup | Pakette doğrulanan bilgi |
| --- | --- |
| `app/base/zone00.bin`…`zone17.bin` | Ardışık 18 dosyanın her biri 4.194.304 bayt. |
| `app/base/zone00_height.bin`…`zone17_height.bin` | Aynı 18 numaraya ait dosyaların her biri 16.777.216 bayt. |
| `app/base/zone00_ls.jpg`…`zone17_ls.jpg` | Her bölge numarası için bir JPEG var. Dosya adı tek başına oyuncuya gösterilen semt adını doğrulamıyor. |
| `app/base/objects.dat` | 607.138.652 bayt. Başlangıçta `SKYF`, ardından `01 00` ve `objects` yazıyor. İlk 128 KiB içinde `AGAH.ADF`, `AGOP.ADF`, `BALIKCI.ADF`, `AKTAR.ADF` ve adları ekipman parçalarını çağrıştıran ADF etiketleri bulunuyor. |
| `app/base/textures_1.DAT` | `SKYF` imzalı. Örnek pencerede `BeyazBuyucuDiffuse.dds` ve `BeyazBuyucuNormal.dds` gibi doku adları bulunuyor. Bu etiketler tek başına belirli bir modelle doku eşleşmesini göstermiyor. |
| `app/base/objects/items/ID_ITEM_BOX.ADF` | Paket dışında arama yapmadan incelenebilen bağımsız bir ADF örneği. İlk etiketi `root`, ardından küçük uçlu 32 bit tamsayı olarak `6` geliyor. Dosyada `cuvaldiffuse.dds` etiketi var. |
| `app/base/data/animation.dat` | 1.144.033 bayt. İlk 128 KiB örneğinde okunabilir dosya referansı bulunamadı. Animasyon ve iskelet bağlama yöntemi bu örnekten doğrulanamadı. |

## zone00 arazi doğrulaması

Yükseklik dosyasındaki 4.194.304 hücreyi küçük uçlu 32 bit kayan noktalı sayı olarak okuduk. Değerlerin tamamı sonlu. Maske dosyasında yalnızca 0 ve 255 bulunuyor. Tüm koordinatlarda 255 maskesi ile sıfırdan farklı yükseklik eşleşti: 771.782 hücre. İkişer örnek arasındaki ortalama mutlak yükseklik farkı bir hücre ötede 0,84, 2.048 hücre ötede 0,90 ve 1.024 hücre ötede 30,74. Bu desen ve dosya boyutları 2.048 sütunlu raster yorumunu destekliyor. [Izgara ölçümleri](https://github.com/hedefimpex-lgtm/constantine-armageddon-time/actions/runs/42527773145)

Her 16 hücrede bir örnekle oluşturulan model **2.996 köşe ve 3.314 üçgen** içeriyor. OBJ dosyasından tekrar okunan her köşenin yüksekliği orijinal raster ile karşılaştırıldı. Dışa aktarımda X sütun, Z satır, Y ise dosyadaki yüksekliktir. Oyundaki metre ölçeği, kuzey yönü, bölgenin görünen adı ve sahneye yerleştirilen yapılar henüz belirlenmedi. [Gerçek dosyalarla dışa aktarım testi](https://github.com/hedefimpex-lgtm/constantine-armageddon-time/actions/runs/42528864748)

## Karakter kaydı

`objects.dat` içindeki 1.482 veri kaydının dizini 202.986 baytta biter. Kayıtlar 128 baytlık ad alanı, ardından veri başlangıcı ve uzunluğu için iki küçük uçlu 32 bit sayı içerir. Dizin, dosya sınırları ve üye aralıkları doğrulandı. `objects/npc` klasöründe 229, `objects/maps` klasöründe 30 kayıt bulunur.

| Kayıt | Başlangıç (bayt) | Uzunluk (bayt) | Doğrulama |
| --- | ---: | ---: | --- |
| `objects/npc/AGAH.ADF` | 438.666.404 | 316.402 | Dışa aktarılan kaydın SHA-256 değeri `f4332144a36c0916a730ed72e7dc0c39ba839d19cb3102fad2b496c566446a0a` |
| `objects/npc/AGOP.ADF` | 438.982.806 | 324.818 | `root` etiketiyle başlar. |
| `objects/npc/BALIKCI.ADF` | 439.942.553 | 257.680 | `root` etiketiyle başlar. |

AGAH dosyasındaki ilk etiket `root`, 24. bayttaki etiket `mate`. NPC kaydının kimliğini ve sınırlarını doğruladık. Modelin köşe ve üçgen dizileri, dokularla bağlantısı, kemik ağırlıkları ve hareket klipleri ayrıca çözülmeli. Bu test karakteri çizmez.

## Tek EXE ile yerelde dışa aktarma

Python 3.11 veya üstü ve `innoextract` kurulu bilgisayarda depo kökünden çalıştırın. Çıktı dizini yeni olmalı. Kurulumun SHA-256 değeri önce doğrulanır. EXE çalıştırılmadan geçici dizine açılır.

```sh
python3 scripts/original_assets.py --installer "/dosya/yolu/istanbulkur6_0.exe" --out ./zone00-cikti
```

Komut yerel dizine `zone00.obj` ve `AGAH.ADF` yazar. OBJ dosyası ölçülen arazi yüzeyini içerir. ADF dosyası orijinal NPC kaydını olduğu gibi saklar. Özgün model ve doku dosyaları deponun parçası değildir.
