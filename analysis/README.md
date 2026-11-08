# İstanbul Kıyamet Vakti kurulumu

Yayımcının [indirme sayfası](https://www.istanbuloyun.com/download.aspx) iki ayrı dosya sunar. Tek parça kurulumun adı `istanbulkur6_0.exe`, indirme yardımcısının adı `IKVDownloader.exe`. Önceki yerel kontrolde resmî **yardımcı** 2.078.104 bayt uzunluğunda, altı bölümlü bir x86 Windows PE32 dosyasıydı. SHA-256 değeri `1cef6e6fc5afef06dcf1de6ae0213aad45fb55a198a42013bf5b558cef000510`.

**REA kurulum incelemesi** iş akışı resmî tek parça kurulumu indirir, dosyanın tamamını SHA-256 ile özetler ve PE başlığı ile disk üzerindeki bölümlerin kopyasında REA 6.8.0 ile DLL içe aktarımlarını okur. Arşiv verileri PE görüntüsünden ayrı tutulur. Kurucunun içe aktarımları tek başına oyun motorunu veya ağ protokolünü göstermez.

Aynı testi elinizdeki WeTransfer kopyasıyla çalıştırmak için Python 3.11+ ve REA 6.8.0 bulunan makinede:

```sh
python3 scripts/inspect-installer.py /dosya/yolu/istanbulkur6_0.exe build/rea/yerel.json
```

İki dosyanın aynı sürüm olduğuna karar vermek için tam dosya SHA-256 değerlerini karşılaştırın. Ardından kurulumun içerik listesini ve asıl oyun istemcisini ayrı örnekler olarak inceleyin.
