# 🎵 하모니아 (Harmonia) — 세계 음악 역사 플랫폼

하모니아는 21만 곡의 방대한 MIDI 아카이브를 기반으로 인류의 음악 역사를 탐험하고 감상할 수 있는 유튜브식 스트리밍 플랫폼입니다.

## 🚀 핵심 기능
- **🌍 세계 음악 아카이브**: 217,882곡의 대규모 MIDI 데이터셋 인덱싱 완료.
- **⚡ 유튜브식 스트리밍**: Google Cloud Storage(GCS) 연동을 통한 즉시 재생 및 무한 확장 구조.
- **📜 역사적 연대기**: 고대 그리스(BC 1400)부터 현대까지, 한국과 세계의 음악사를 비교 감상.
- **📺 테마별 채널**: 클래식 거장, 한국의 소리, 힐링 피아노 등 큐레이션 플레이리스트 제공.
- **🔍 초고속 검색**: SQLite 기반 전역 검색 엔진으로 원하는 곡을 0.1초 만에 탐색.

## 🏗️ 시스템 아키텍처
- **Frontend**: Vanilla JS (Tone.js + @tonejs/midi), Dark Mode, Responsive Design.
- **Backend**: Python-based GCS Cloud-Native Server.
- **Storage**: Google Cloud Storage (gs://harmonia-midi) 독립형 파일 관리.
- **Database**: SQLite (harmonia.db) 메타데이터 인덱싱.

## 🛠️ 관리 도구 (Scripts)
- `scripts/add_song.py`: 새로운 곡 및 메타데이터 추가 CLI.
- `scripts/enrich_catalog.py`: 대규모 데이터 메타데이터(작곡가, 시대, 태그) 부착 도구.
- `scripts/upload_to_gcs.py`: MIDI 파일 및 DB를 클라우드 저장소로 업로드.

## 📦 데이터셋 구성
- **Lakh MIDI**: 195,817곡 (팝/록/재즈 전 장르)
- **ADL Piano**: 11,087곡 (클래식/뉴에이지 피아노)
- **Historical World**: 2,754곡 (세계 각국 전통 음악)
- **Mutopia Project**: 1,529곡 (상업 활용 가능 클래식 거장곡)
- **Korean Jeongganbo**: 170곡 (시김새 v2 반영 정악 및 민속악)

---
*세종대왕의 정간보(1447) 정신을 21세기 디지털 기술로 계승합니다.*
