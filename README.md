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

Sağlık yanıtı `{"ok":true,"version":1}` olmalıdır. Oyun sunucusu makinenin yerel 8787 portunda dinler.

### Telefondan bağlanma

1. Kullanacağınız alan adının DNS A kaydını VPS’nizin genel IPv4 adresine yönlendirin.
2. VPS’de zaten bir HTTPS ters vekili çalışıyorsa, bu alan adını `127.0.0.1:8787` adresine bağlayın. [Mevcut Caddy için örnek](deploy/Caddyfile.example).
3. 80 ve 443 numaralı TCP portları kullanılmıyorsa ve dışarıdan erişilebiliyorsa, depodaki ağ geçidini kullanabilirsiniz. Aşağıdaki örnek alan adını kendinize ait alan adıyla değiştirin.

```sh
export GAME_DOMAIN=oyun.ornek.com
docker compose -f compose.yaml -f deploy/https.compose.yaml up -d --build --wait
curl -fsS "https://$GAME_DOMAIN/health"
```

HTTPS sağlık denetimi başarılı olduğunda Android uygulamasında **Birlikte oyna** bölümüne aynı `https://` adresini girin. Caddy sertifikaları adlandırılmış Docker birimlerinde saklar.

## REA incelemesi

[İnceleme notları](analysis/README.md) ikili dosya incelemesinin kapsamını ve nasıl yineleneceğini açıklar. Çalışma akışı yalnızca rapor üretir. Mobil prototipin çizimleri, oyun kuralları ve sunucu kodu bu depo için yazılmıştır.
