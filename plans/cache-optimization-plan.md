# Cache Optimization Plan - Non-Base Payload Selective Caching

**Status:** ⏸️ Beklemede (Kullanıcı UX yaklaşımı üzerinde düşünüyor)
**Tarih:** 2026-03-30

---

## Özet

Base (minimum gerekli) olmayan payload'lar artık otomatik olarak AppCache'e eklenmeyecek. Kullanıcı ayarlardan aktif ederse cache'e eklenebilecek.

**Mevcut cache boyutu:** ~16 MB (tüm default payload'lar)
**Hedef cache boyutu:** ~5-9 MB (yaklaşıma göre değişir)
**Tahmini tasarruf:** %40-67

---

## Mevcut Cache Sistemi

### Katman 1 - AppCache (build-time)
- `appcache_manifest_generator.py` → `cache.appcache` manifest üretir
- `payload_map.js` içinde `isDefault: true` olan version'ların binary'leri eklenir
- Metadata.json dosyaları + core JS/CSS/offsets her zaman eklenir
- **Garantili offline çalışma**

### Katman 2 - HTTP Cache (runtime)
- `preFetchSelectedPayloads()` ayarlardan çıkarken non-default seçimleri `fetch()` ile cache'e alır
- **Best-effort offline** (tarayıcı temizleyebilir)

---

## Mevcut Cache İçeriği ve Boyutları

| Payload | Boyut | Kullanım |
|---------|-------|----------|
| etaHEN 2.4B | 4.6 MB | Çok yüksek |
| kstuff-lite 1.1-dr | 1.5 MB | Yüksek (etaHEN içinde var) |
| kstuff 1.5 | 1.4 MB | Düşük (eski) |
| kstuff-lite-1200 | 1.5 MB | Çok düşük (FW 12 only) |
| websrv 0.30 | 1.4 MB | Orta |
| shadowmountplus 1.6test7 | 1.3 MB | Orta |
| libhijacker 1.160 | 1.1 MB | Düşük |
| shsrv 0.18 | 0.9 MB | Düşük |
| elfldr 0.22.1 | 0.4 MB | Yüksek |
| byepervisor 1.1 | 0.3 MB | Düşük |
| ftpsrv 0.18.2 | 0.2 MB | Orta |
| ps5debug-dizz | 0.2 MB | Çok düşük |
| ps5debug 1.0b5 | 0.1 MB | Çok düşük |
| klogsrv 0.7.1 | 0.1 MB | Çok düşük |
| kstuff-toggle 0.2 | 0.1 MB | Çok düşük |
| rp-get-pin 0.1.1 | 0.1 MB | Çok düşük |
| backpork 0.1 | 0.1 MB | Çok düşük |
| ps5-versions 1.0 | 0.01 MB | Çok düşük |
| **Toplam** | **~15.3 MB** | |
| + metadata + core | **~16.2 MB** | |

---

## UX Yaklaşım Seçenekleri (Karar Bekleniyor)

### A) Minimal (~5 MB)
- Base: etaHEN + elfldr
- Diğerleri için ayrı ayrı toggle
- Pro: En fazla tasarruf
- Con: Kullanıcı her şeyi tek tek seçmeli

### B) Hybrid (~6.5 MB + "Cache All" butonu)
- Base: etaHEN + elfldr + kstuff-lite
- "Cache All" butonu ile tek seferde tümü aktif
- Pro: Hızlı toplu işlem
- Con: Biraz daha karmaşık UI

### C) Recommended (~9 MB)
- Base: etaHEN + elfldr + kstuff-lite + websrv + ftpsrv
- Sadece nadir kullanılanlar toggle ile
- Pro: Çoğu kullanıcı için yeterli
- Con: Az tasarruf

### D) Sürükle-bırak sıralama
- En üstteki payload'lar cache'lenir
- Pro: Esnek
- Con: Karmaşık implementasyon

---

## Teknik Değişiklik Planı

### Dosya Değişiklikleri

1. **metadata.json** - `isBasePayload: true/false` alanı eklenir
2. **appcache_manifest_generator.py** - `isBasePayload` filtresi eklenir
3. **constants.js** - `SETTINGS_PAYLOAD_CACHE` localStorage key
4. **settings-manager.js** - `isPayloadCacheEnabled()`, `setPayloadCacheEnabled()`, `isBasePayload()`, `loadCacheSettings()`, `saveCacheSettings()`
5. **version-selection.js** - "Cache for Offline" toggle butonu (non-base payload'lar için)
6. **settings-view.js** - `preFetchSelectedPayloads()` sadece cache-enabled payload'ları fetch eder
7. **main.css** - `.version-cache-btn`, `.version-card-cached-badge` stilleri

### Cache Toggle Davranışı

- Per-payload toggle (payload bazlı, version bazlı değil)
- localStorage'da `payload_cache_enabled` key'inde saklanır
- Version değişse bile toggle aktif kalır → otomatik güncelleme
- `preFetchSelectedPayloads()` ayarlardan çıkarken cache-enabled payload'ları fetch eder

### Badge Sistemi

- Base payload → "Always Available" badge
- Cache-enabled non-base → "Cached" badge
- Cache-disabled non-base → badge yok

---

## Akış Diyagramı

```
İlk Yükleme → AppCache (base payloadlar: etaHEN + elfldr ~ 5MB)
     ↓
Ayarlar → Payload seç → "Cache for Offline" toggle
     ↓
Toggle ON → fetch(payload.elf) → HTTP cache → "Cached" badge
     ↓
Güncelleme → preFetchSelectedPayloads() → yeni version otomatik fetch
     ↓
Toggle OFF → cache temizlenmez ama yenisi fetch edilmez
```

---

## Notlar

- kstuff-lite etaHEN içinde zaten var, ayrı base yapmaya gerek yok olabilir
- AppCache garantili offline, HTTP cache best-effort
- PS5 browser cache limitleri göz önünde bulundurulmalı
- Mevcut `preFetchSelectedPayloads()` mekanizması genişletilerek kullanılacak
