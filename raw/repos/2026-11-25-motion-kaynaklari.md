# Motion kaynakları (kullanıcının verdiği altı kaynak), 2026-11-25

Ham not. Repolar `git clone --depth 1` ile okundu; kopyalanan dosyalar `.claude/skills/gsap-*`, `.claude/skills/threejs-*` (LICENSE ile) ve `library/vendor/gsap/`.

| Kaynak | Adres | Lisans | İçerik |
|---|---|---|---|
| Prompt Motion | https://prompt-motion.com/ | Site içeriği gönderenlerin | 240 motion videosu ve arkasındaki prompt. Prompt'lar `<inputs>`, `<direction>`, `<structure>`, `<build>`, `<gotchas>` bölümlerinden oluşur. Örnek ("Orange dot motion system"): tek turuncu nokta tüm sahneleri bağlar; yasak listesi (stok görüntü, degrade, parıltı, rastgele geçiş); 60 fps tek HTML, her görsel seek(t) içinde zamandan hesaplanır; kapalı-form yaylar; grafik ve nokta aynı yay fonksiyonundan; ölçülen beat'e senkron; tam export öncesi beat başına tek kare. |
| threejs-skills | https://github.com/CloudAI-X/threejs-skills | MIT | 13 skill (fundamentals, geometry, materials, lighting, textures, shaders, postprocessing, animation, loaders, performance, interaction, react-three-fiber, asset-pipeline); three.js r186 hedefli, WebGPU/TSL bölümleriyle. |
| pascalorg/editor | https://github.com/pascalorg/editor | MIT | AECO 3D bina editörü (React Three Fiber + WebGPU), MCP sunucusu, CLI. Video üretimine doğrudan uymaz. |
| gsap-skills | https://github.com/greensock/gsap-skills | MIT (GSAP: standart ücretsiz lisans) | Resmî GSAP skill'leri: core, timeline, plugins, utils, performance, scrolltrigger, react, frameworks. |
| motion-design-skill | https://github.com/LottieFiles/motion-design-skill | MIT | Yönetmen katmanı: üç sütun, dört hareket kişiliği, duygu-hareket haritası, Disney ilkeleri, koreografi, 1/3 kuralı, süre ve eğri tabloları. |
| video-shotcraft | https://github.com/Vincentwei1021/video-shotcraft | Apache-2.0 | 124 çekim kartı / 150 çekim (Remotion), Ink Press şablonu, beat-sync ve ses tasarımı, kare QA. Kartlar 2026-11-16'dan beri `library/vendor/video-shotcraft/` altında yalnız referans. |
