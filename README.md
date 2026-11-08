# Constantine · Armageddon Time

Karaköy rıhtımında geçen özgün, iki boyutlu bir mobil oyun prototipi. Zemine dokunarak yürüyün. Üç rölenin her birine yaklaşıp **Röleyi etkinleştir** düğmesine basın. Tek oyunculu görev Android paketinde çevrimdışı çalışır. Çevrim içi modda aynı odadaki oyuncular birbirini görür. Görev ilerlemesi oyuncu başına tutulur ve oturum kapanınca sıfırlanır.

## Android ve tarayıcı

GitHub Actions içindeki **Mobil prototip** çalışmasının `constantine-android` çıktısı test APK'sını içerir. Android 8 veya üstü ve güncel Android System WebView gerekir. Deneme paketleri geçici anahtarla imzalanır. Daha önce farklı bir test sürümü kurulduysa yenisini kurmadan önce eskisini kaldırmak gerekebilir.

Tarayıcıda denemek için Node.js 22 veya üstüyle depo kökünde çalıştırın.

```sh
node --test server/server.test.cjs
node server/server.cjs
```

Aynı bilgisayarda `http://127.0.0.1:8787` adresini açın. İki ayrı sekmede **Birlikte oyna** seçilince karakterler aynı odaya girer. Sunucu hareket hızını, harita sınırını ve röleye uzaklığı denetler. Oda en çok 64 aktif oturum alır. Kimlikler beş dakikalık hareketsizlikten sonra sona erer.

## VPS kurulumu

Docker Engine ve Compose eklentisi kurulu Linux sunucuda aşağıdaki komutları çalıştırın. Sunucunuzda depo zaten varsa mevcut kopyayı kullanın.

```sh
git clone https://github.com/hedefimpex-lgtm/constantine-armageddon-time.git
cd constantine-armageddon-time
docker compose up -d --build
curl -fsS http://127.0.0.1:8787/health
```

Sağlık yanıtı `{"ok":true,"version":1}` olmalıdır. Oyun yalnızca sunucunun yerel 8787 portunda dinler. Telefondan bağlanmak için bir alan adını VPS'ye yönlendirin ve mevcut HTTPS ters vekilinizi bu porta bağlayın. Caddy kullanıyorsanız [örnek yapılandırmadaki](deploy/Caddyfile.example) alan adını kendi adınızla değiştirip mevcut yapılandırmanıza ekleyin. Android uygulamasında **Birlikte oyna** bölümüne aynı HTTPS adresini girin.

## REA incelemesi

[İnceleme notları](analysis/README.md) ikili dosya incelemesinin kapsamını ve nasıl yineleneceğini açıklar. Çalışma akışı yalnızca rapor üretir. Mobil prototipin çizimleri, oyun kuralları ve sunucu kodu bu depo için yazılmıştır.
