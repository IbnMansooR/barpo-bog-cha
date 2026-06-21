# BĀRPO — 3D modellar

Har qanday qurilmada (kompyuter, planshet, telefon) 3D modellarni ko'rish uchun web sahifa.
[`<model-viewer>`](https://modelviewer.dev/) asosida, telefonda **AR** qo'llab-quvvatlanadi.

## Model qo'shish

1. `.glb` (yoki `.gltf`) fayllarni `models/` papkasiga tashlang.
2. Skriptni ishga tushiring:
   ```bash
   node generate.mjs
   ```
   Bu `models.json` ni avtomatik yangilaydi (nom, hajm, ixtiyoriy thumbnail).
3. Git'ga yuklang — Vercel o'zi qayta deploy qiladi:
   ```bash
   git add . && git commit -m "Yangi modellar" && git push
   ```

> Faqat **`.glb` / `.gltf`** formati ko'rsatiladi. Boshqa format (`.obj`, `.fbx`, `.skp`, `.max`, `.blend` ...) bo'lsa avval GLB ga konvertatsiya qiling.

## Thumbnail (ixtiyoriy)

Galereyada model o'rniga rasm ko'rsatish uchun `thumbnails/` papkasiga model bilan bir xil nomli `.webp/.png/.jpg` qo'ying (masalan `models/stol.glb` → `thumbnails/stol.png`).

## Tuzilishi

| Fayl | Vazifasi |
|------|----------|
| `index.html` | Galereya — barcha modellar ro'yxati |
| `viewer.html` | Bitta modelni to'liq ekranda + AR |
| `models/` | `.glb` model fayllari |
| `thumbnails/` | Ixtiyoriy oldindan ko'rish rasmlari |
| `models.json` | `generate.mjs` yasaydigan manifest |
| `generate.mjs` | `models/` ni skanlab manifest yasaydi |
