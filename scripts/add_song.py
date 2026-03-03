#!/usr/bin/env python3
"""
하모니아(Harmonia) 곡 추가 CLI
Usage:
  python3 scripts/add_song.py --file song.mid --region korean --group "영산회상" \
    --title "영산회상 가락덜이" --composer "전통" --year 1500 --era "조선" --tags "정악,풍류"

  python3 scripts/add_song.py --batch songs.json   # JSON 배치 추가
  python3 scripts/add_song.py --list                # 전체 곡 목록
  python3 scripts/add_song.py --stats               # 통계
  python3 scripts/add_song.py --verify              # 데이터 무결성 검증
"""
import json, os, sys, argparse, shutil
from datetime import datetime

CATALOG = os.path.join(os.path.dirname(__file__), '..', 'catalog.json')
MIDI_BASE = os.path.join(os.path.dirname(__file__), '..', 'static', 'midi')

def load_catalog():
    with open(CATALOG, encoding='utf-8') as f:
        return json.load(f)

def save_catalog(cat):
    with open(CATALOG, 'w', encoding='utf-8') as f:
        json.dump(cat, f, ensure_ascii=False, indent=2)
    print(f"✅ catalog.json 저장 완료")

def find_region(cat, region_id):
    return next((r for r in cat["regions"] if r["id"] == region_id), None)

def find_group(region, group_name):
    return next((g for g in region.get("groups", []) if g["name"] == group_name), None)

def add_song(cat, args):
    """Add a single song to the catalog"""
    region = find_region(cat, args.region)
    if not region:
        # Create new region
        region = {
            "id": args.region,
            "name": args.region_name or args.region,
            "emoji": args.emoji or "🎵",
            "songCount": 0,
            "description": args.description or "",
            "basePath": f"/static/midi/world/{args.region}/",
            "groups": []
        }
        cat["regions"].append(region)
        print(f"  📁 새 지역 생성: {args.region}")
    
    group = find_group(region, args.group)
    if not group:
        group = {
            "name": args.group,
            "era": args.era or "",
            "year": args.year,
            "history": args.history or "",
            "tracks": []
        }
        region["groups"].append(group)
        print(f"  📂 새 그룹 생성: {args.group}")
    
    # Check duplicate
    if any(t["file"] == os.path.basename(args.file) for t in group["tracks"]):
        print(f"  ⚠️ 이미 존재: {args.file}")
        return False
    
    # Copy MIDI file if source path provided
    filename = os.path.basename(args.file)
    if args.region == "korean":
        dest_dir = MIDI_BASE
    else:
        dest_dir = os.path.join(MIDI_BASE, "world", args.region)
    
    os.makedirs(dest_dir, exist_ok=True)
    
    if os.path.exists(args.file) and not os.path.exists(os.path.join(dest_dir, filename)):
        shutil.copy2(args.file, os.path.join(dest_dir, filename))
        print(f"  📋 파일 복사: {filename} → {dest_dir}")
    
    # Add track
    track = {
        "title": args.title or filename.replace('.mid', '').replace('_', ' '),
        "file": filename,
        "composer": args.composer or "작자 미상",
        "year": args.year or 1800,
        "era": args.era or "",
        "tags": [t.strip() for t in (args.tags or "").split(",")] if args.tags else [],
    }
    if args.title_ko:
        track["title_ko"] = args.title_ko
    
    group["tracks"].append(track)
    
    # Update counts
    total = sum(len(t) for g in region["groups"] for t in [g.get("tracks", [])])
    region["songCount"] = total
    cat["totalSongs"] = sum(r.get("songCount", 0) for r in cat["regions"])
    
    print(f"  ✅ 추가: {track['title']} ({track['composer']}, {track['year']})")
    return True

def batch_add(cat, json_path):
    """Add songs from a JSON file"""
    with open(json_path, encoding='utf-8') as f:
        songs = json.load(f)
    
    added = 0
    for song in songs:
        ns = argparse.Namespace(**song)
        if add_song(cat, ns):
            added += 1
    
    print(f"\n📊 배치 추가 완료: {added}/{len(songs)}곡")
    return added

def list_songs(cat):
    """List all songs"""
    total = 0
    for r in cat["regions"]:
        print(f"\n{'='*60}")
        print(f"{r.get('emoji', '🎵')} {r['name']} ({r.get('songCount', 0)}곡)")
        print(f"{'='*60}")
        for g in r.get("groups", []):
            print(f"\n  📂 {g['name']} ({len(g.get('tracks',[]))}곡)")
            for t in g.get("tracks", []):
                composer = t.get("composer", "?")
                year = t.get("year", "?")
                tags = ", ".join(t.get("tags", []))
                print(f"    ♪ {t['title']}  |  {composer}  |  {year}  |  {tags}")
                total += 1
    print(f"\n총 {total}곡")

def stats(cat):
    """Show statistics"""
    total = 0
    by_region = {}
    by_era = {}
    composers = set()
    year_min = 9999
    year_max = -9999
    missing_composer = 0
    missing_tags = 0
    
    for r in cat["regions"]:
        count = 0
        for g in r.get("groups", []):
            for t in g.get("tracks", []):
                total += 1
                count += 1
                c = t.get("composer", "")
                if c and c != "작자 미상": composers.add(c)
                if not c: missing_composer += 1
                if not t.get("tags"): missing_tags += 1
                y = t.get("year", 0)
                if y: 
                    year_min = min(year_min, y)
                    year_max = max(year_max, y)
                era = t.get("era", "미분류")
                by_era[era] = by_era.get(era, 0) + 1
        by_region[f"{r.get('emoji','')} {r['name']}"] = count
    
    print("📊 하모니아 통계")
    print(f"{'='*50}")
    print(f"총 곡 수: {total}")
    print(f"지역 수: {len(cat['regions'])}")
    print(f"식별된 작곡가: {len(composers)}명")
    print(f"연도 범위: BC {abs(year_min)} ~ AD {year_max}")
    print(f"작곡가 미상: {missing_composer}곡")
    print(f"태그 없음: {missing_tags}곡")
    print(f"\n📌 지역별:")
    for name, cnt in sorted(by_region.items(), key=lambda x: -x[1]):
        print(f"  {name}: {cnt}곡")
    print(f"\n📌 시대별 (상위 15):")
    for era, cnt in sorted(by_era.items(), key=lambda x: -x[1])[:15]:
        print(f"  {era}: {cnt}곡")

def verify(cat):
    """Verify data integrity"""
    errors = []
    warnings = []
    total = 0
    
    for r in cat["regions"]:
        rid = r["id"]
        if rid == "korean":
            base = MIDI_BASE
        else:
            base = os.path.join(MIDI_BASE, "world", rid)
        
        for g in r.get("groups", []):
            for t in g.get("tracks", []):
                total += 1
                fn = t.get("file", "")
                
                # Check file exists
                fpath = os.path.join(base, fn)
                if not os.path.exists(fpath):
                    errors.append(f"❌ 파일 없음: {fn} (지역: {rid})")
                
                # Check required fields
                if not t.get("composer"):
                    warnings.append(f"⚠️ 작곡가 없음: {t.get('title', fn)}")
                if not t.get("year"):
                    warnings.append(f"⚠️ 연도 없음: {t.get('title', fn)}")
                if not t.get("tags"):
                    warnings.append(f"⚠️ 태그 없음: {t.get('title', fn)}")
    
    print(f"🔍 데이터 무결성 검증 ({total}곡)")
    print(f"{'='*50}")
    if errors:
        print(f"\n❌ 오류 {len(errors)}건:")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... +{len(errors)-20}건")
    else:
        print("✅ 파일 누락 없음")
    
    if warnings:
        print(f"\n⚠️ 경고 {len(warnings)}건:")
        for w in warnings[:20]:
            print(f"  {w}")
        if len(warnings) > 20:
            print(f"  ... +{len(warnings)-20}건")
    else:
        print("✅ 메타데이터 완전")
    
    return len(errors) == 0

def main():
    parser = argparse.ArgumentParser(description="하모니아 곡 관리 CLI")
    parser.add_argument("--list", action="store_true", help="전체 곡 목록")
    parser.add_argument("--stats", action="store_true", help="통계")
    parser.add_argument("--verify", action="store_true", help="데이터 무결성 검증")
    parser.add_argument("--batch", help="JSON 파일로 배치 추가")
    parser.add_argument("--file", help="MIDI 파일 경로")
    parser.add_argument("--region", help="지역 ID (korean, europe_medieval, ...)")
    parser.add_argument("--region-name", help="지역 표시 이름")
    parser.add_argument("--emoji", help="지역 이모지")
    parser.add_argument("--description", help="지역 설명")
    parser.add_argument("--group", help="그룹 이름")
    parser.add_argument("--title", help="곡 제목")
    parser.add_argument("--title-ko", help="한국어 제목")
    parser.add_argument("--composer", help="작곡가")
    parser.add_argument("--year", type=int, help="작곡 연도")
    parser.add_argument("--era", help="시대")
    parser.add_argument("--tags", help="태그 (콤마 구분)")
    parser.add_argument("--history", help="그룹 역사 해설")
    
    args = parser.parse_args()
    cat = load_catalog()
    
    if args.list:
        list_songs(cat)
    elif args.stats:
        stats(cat)
    elif args.verify:
        verify(cat)
    elif args.batch:
        batch_add(cat, args.batch)
        save_catalog(cat)
    elif args.file:
        if not args.region or not args.group:
            print("❌ --region과 --group은 필수입니다")
            sys.exit(1)
        add_song(cat, args)
        save_catalog(cat)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
