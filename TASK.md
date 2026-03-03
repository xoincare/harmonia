# MidiTube — World Music History Site Rebuild

## Overview
Transform the existing Korean traditional music (gugak-history) site into **MidiTube** — a world music history learning platform with in-browser MIDI playback.

## Current State
- `index.html` (403 lines) — Korean music history with timeline, instruments, YouTube embeds, MIDI player for 91 Korean pieces
- `static/css/style.css` (276 lines) — existing styles
- `static/js/midi-player.js` (353 lines) — Tone.js MIDI player for Korean pieces only
- `static/midi/` — 91 Korean jeongganbo MIDI files
- `static/midi/world/` — world MIDI files organized by region (just copied)
- `server.py` + `Dockerfile` — Python server for Cloud Run

## MIDI File Structure
```
static/midi/                          # 91 Korean traditional (jeongganbo)
static/midi/world/
  ancient_greco_roman/    15 files    # Seikilos Epitaph, Delphic Hymns, Mesomedes etc.
  asia_traditional/       13 files    # Chinese traditional
  celtic/                 50 files    # Celtic folk
  europe_folk/           160 files    # European folk songs
  europe_medieval/       102 files    # Medieval & Renaissance
  india/                  20 files    # Indian raga
  korean_traditional/      3 files    # Additional Korean folk
  latin_america/          55 files    # Venezuelan & Latin American
  middle_east/          2200 files    # Turkish makam (SymbTr) — TOO MANY, select ~100 representative
  national_anthems/      139 files    # National anthems worldwide
```

## Requirements

### 1. Site Identity
- Title: **하모니아 Harmonia — 세계 음악의 역사**
- Tagline: "고대 그리스부터 동아시아까지, 세계 음악을 듣고 배우세요"
- Brand name origin: Harmonia = 그리스 신화의 조화의 여신
- Keep Korean as primary language
- Modern, clean design (dark theme preferred, music-app feel)

### 2. Navigation & Regions
Main regions with emoji flags:
- 🇰🇷 한국 전통음악 (91 jeongganbo + 3 folk)
- 🏛️ 고대 그리스·로마 (15)
- 🏰 유럽 중세·르네상스 (102)
- 🎻 유럽 민속음악 (160)
- 🍀 켈틱 (50)
- 🕌 중동·터키 마캄 (~100 selected)
- 🇮🇳 인도 라가 (20)
- 🇨🇳 중국 전통 (13)
- 💃 라틴 아메리카 (55)
- 🏳️ 세계 국가(國歌) (139)

### 3. Page Structure
- **Hero**: MidiTube branding, total song count, search bar
- **Region Cards**: Grid of region cards with icon, name, song count, brief description. Click → region detail
- **Region Detail View** (can be same page with JS show/hide or separate sections):
  - Brief historical context (2-3 paragraphs in Korean)
  - Timeline if applicable
  - Song list with MIDI player
- **MIDI Player**: Upgrade existing Tone.js player to work with all regions
  - Song list per region with search/filter
  - Play/pause/stop, progress bar, volume
  - Show current playing song title
  - Auto-next in playlist mode
- **Korean Section**: Keep ALL existing content (history timeline, jeongganbo explanation, instruments, Jongmyo, YouTube embeds, open source section). This should be the most detailed section.

### 4. Turkish Makam Selection
The middle_east/ folder has 2200 Turkish makam files. Create a curated selection of ~100:
- Pick diverse makam types (look at filenames for makam names)
- Rename/organize for display
- Store full list in a JSON catalog but only show 100 in UI

### 5. Technical
- Keep single-page app approach (no framework, vanilla JS + HTML + CSS)
- Use existing Tone.js + @tonejs/midi setup from midi-player.js
- MIDI files served as static assets
- Generate a `catalog.json` with metadata for all songs (region, title, filename, description if available)
- Keep `server.py` and `Dockerfile` working
- Mobile responsive

### 6. Historical Context (write in Korean)
Add brief Korean-language descriptions for each region:
- 🏛️ 고대 그리스·로마: 세이킬로스 비문(기원전 200년경), 델피 찬가, 메소메데스 등 현존 최고(最古) 악보
- 🏰 유럽 중세: 그레고리안 성가, 트루바두르, 기욤 드 마쇼 등
- 🎻 유럽 민속: 각 국가별 전통 민요
- 🍀 켈틱: 아일랜드·스코틀랜드 전통 음악
- 🕌 터키 마캄: 오스만 제국 궁정 음악 체계, 마캄(선법) 기반
- 🇮🇳 인도 라가: 힌두스탄·카르나틱 전통, 라가(선율형)와 탈라(리듬형)
- 🇨🇳 중국 전통: 고쟁, 얼후, 비파 등 전통 악기
- 💃 라틴: 안데스, 베네수엘라 전통 음악
- 🏳️ 국가: 각국 국가의 음악적 의미

### 7. Preserve
- ALL existing Korean content (history, jeongganbo, instruments, YouTube, open source)
- git history
- server.py / Dockerfile compatibility

## Output
Modify files in place. Commit when done with message: "feat: Harmonia — 세계 음악 역사 사이트 리빌드"

Do NOT use any external APIs or CDNs other than what's already used (Google Fonts, Tone.js CDN).
