#!/usr/bin/env python3
"""Generate catalog.json from actual MIDI files on disk."""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
MIDI_ROOT = os.path.join(BASE, "static", "midi")
WORLD = os.path.join(MIDI_ROOT, "world")


def title_from_filename(fname):
    """Convert filename to display title."""
    name = fname.replace(".mid", "")
    # Turkish makam: makam--form--usul--title--composer
    if "--" in name:
        parts = name.split("--")
        makam = parts[0].replace("_", " ").title()
        form_ = parts[1].replace("_", " ").title() if len(parts) > 1 else ""
        title = parts[3].replace("_", " ").title() if len(parts) > 3 else ""
        composer = parts[4].replace("_", " ").title() if len(parts) > 4 else ""
        display = makam
        if form_:
            display += f" — {form_}"
        if title and title.strip():
            display += f" — {title}"
        if composer and composer.strip():
            display += f" ({composer})"
        return display
    # Hyphenated: amazing-grace-piano.mid
    if "-" in name:
        return name.replace("-", " ").title()
    # Underscored
    if "_" in name:
        return name.replace("_", " ").title()
    # CamelCase or plain
    return name.replace("_", " ").title()


def scan_dir(dirpath):
    """Return sorted list of .mid files in a directory."""
    files = []
    for f in sorted(os.listdir(dirpath)):
        if f.lower().endswith(".mid"):
            files.append(f)
    return files


def make_tracks(files):
    """Convert filenames to track entries."""
    return [{"title": title_from_filename(f), "file": f} for f in files]


# === Korean Jeongganbo (preserve existing grouped structure) ===
korean_groups = [
    {
        "name": "영산회상 (현악 9곡)",
        "era": "조선 초기~후기",
        "tracks": []
    },
    {
        "name": "관악영산회상 (8곡)",
        "era": "조선 후기",
        "tracks": []
    },
    {
        "name": "평조회상 (8곡)",
        "era": "조선 후기",
        "tracks": []
    },
    {
        "name": "독립곡 (4곡)",
        "era": "백제~조선 세종",
        "tracks": []
    },
    {
        "name": "도드리·천년만세 (5곡)",
        "era": "조선 후기",
        "tracks": []
    },
    {
        "name": "취타·현악취타 (10곡)",
        "era": "조선 초기~후기",
        "tracks": []
    },
    {
        "name": "남창 우조 가곡 (11곡)",
        "era": "조선 중기~후기",
        "tracks": []
    },
    {
        "name": "남창 계면 가곡 (13곡)",
        "era": "조선 중기~후기",
        "tracks": []
    },
    {
        "name": "남창 반우반계 (2곡)",
        "era": "조선 후기",
        "tracks": []
    },
    {
        "name": "여창 우조 가곡 (5곡)",
        "era": "조선 후기",
        "tracks": []
    },
    {
        "name": "여창 계면 가곡 (7곡)",
        "era": "조선 후기",
        "tracks": []
    },
    {
        "name": "여창 반우반계 (2곡)",
        "era": "조선 후기",
        "tracks": []
    },
    {
        "name": "자진한잎 (7곡)",
        "era": "조선 중기~후기",
        "tracks": []
    },
]

# Map prefixes to groups
prefix_map = {
    "영산회상": 0, "관악영산회상": 1, "평조회상": 2,
    "수제천": 3, "여민락": 3, "동동": 3, "보허자": 3,
    "밑도드리": 4, "웃도드리": 4, "천년만세": 4,
    "취타": 5, "현악취타": 5,
    "남창우조": 6, "남창계면": 7, "남창반우반계": 8,
    "여창우조": 9, "여창계면": 10, "여창반우반계": 11,
    "자진한잎": 12,
}

korean_files = scan_dir(MIDI_ROOT)
for f in korean_files:
    name = f.replace(".mid", "")
    # Extract display name: first part before underscore instruments
    parts = name.split("_")
    display = parts[0]  # Korean name part

    # Find matching group
    matched = False
    for prefix, idx in prefix_map.items():
        if name.startswith(prefix):
            korean_groups[idx]["tracks"].append({"title": display, "file": f})
            matched = True
            break
    if not matched:
        # Put in independent group
        korean_groups[3]["tracks"].append({"title": display, "file": f})

# Also add the 3 folk songs from korean_traditional
korean_folk_dir = os.path.join(WORLD, "korean_traditional")
korean_folk_files = scan_dir(korean_folk_dir)
korean_folk_group = {
    "name": "한국 민요 (3곡)",
    "era": "전통",
    "tracks": make_tracks(korean_folk_files)
}

korean_all_groups = korean_groups + [korean_folk_group]
korean_count = sum(len(g["tracks"]) for g in korean_all_groups)


# === World Regions ===
def make_region(id_, name, emoji, desc, dirpath, base_path, group_name=None):
    files = scan_dir(dirpath)
    tracks = make_tracks(files)
    groups = [{"name": group_name or name, "tracks": tracks}]
    return {
        "id": id_,
        "name": name,
        "emoji": emoji,
        "songCount": len(tracks),
        "description": desc,
        "basePath": base_path,
        "groups": groups
    }


regions = []

# 1. Korean
regions.append({
    "id": "korean",
    "name": "한국 전통음악",
    "emoji": "🇰🇷",
    "songCount": korean_count,
    "description": "세종대왕의 정간보(1447)로 기록된 궁중정악 91곡과 한국 민요. 동양 최초의 정량 기보법으로 기록된 보태평·정대업·여민락·수제천 등 한국 음악의 정수를 담고 있습니다. 가야금·거문고·대금·피리·해금·아쟁 등 전통 악기의 합주를 MIDI로 재현했습니다.",
    "basePath": "/static/midi/",
    "groups": korean_all_groups
})

# 2. Ancient Greco-Roman
regions.append(make_region(
    "ancient_greco_roman",
    "고대 그리스·로마",
    "🏛️",
    "기원전 1400년 후리안 찬가부터 기원전 200년 세이킬로스 비문까지, 현존하는 세계 최고(最古)의 악보들입니다. 델피 신전의 아폴론 찬가, 메소메데스의 태양신·뮤즈·네메시스 찬가 등 고대 그리스·로마 음악의 실제 선율을 들을 수 있습니다. 비잔틴 성가와 이탈리아 에스탕피도 포함됩니다.",
    os.path.join(WORLD, "ancient_greco_roman"),
    "/static/midi/world/ancient_greco_roman/"
))

# 3. Europe Medieval
regions.append(make_region(
    "europe_medieval",
    "유럽 중세·르네상스",
    "🏰",
    "그레고리안 성가, 트루바두르의 노래, 기욤 드 마쇼의 다성음악부터 르네상스 시대의 무곡과 마드리갈까지. 12~16세기 유럽 음악의 발전 과정을 담고 있습니다. 중세 에스탕피, 칸티가스 데 산타 마리아, 그린슬리브스 등 역사적 명곡들을 포함합니다.",
    os.path.join(WORLD, "europe_medieval"),
    "/static/midi/world/europe_medieval/"
))

# 4. Europe Folk
regions.append(make_region(
    "europe_folk",
    "유럽 민속음악",
    "🎻",
    "영국·독일·프랑스·러시아 등 유럽 각국의 전통 민요와 동요, 행진곡 모음입니다. 그린슬리브스, 올드 랭 사인, 어메이징 그레이스, 코로베이니키(테트리스 음악), 라 마르세예즈, 스코틀랜드의 용감한 자 등 세계적으로 사랑받는 곡들을 포함합니다.",
    os.path.join(WORLD, "europe_folk"),
    "/static/midi/world/europe_folk/"
))

# 5. Celtic
regions.append(make_region(
    "celtic",
    "켈틱",
    "🍀",
    "아일랜드·스코틀랜드·웨일스의 켈트 전통 음악입니다. 올드 랭 사인, 에리스케이의 사랑 노래, 스카이 섬의 뱃노래 등 켈트 문화의 서정적이고 아름다운 선율을 담고 있습니다. 백파이프·하프·피들로 연주되던 곡들을 MIDI로 재현했습니다.",
    os.path.join(WORLD, "celtic"),
    "/static/midi/world/celtic/"
))

# 6. Middle East (Turkish Makam)
regions.append(make_region(
    "middle_east",
    "중동·터키 마캄",
    "🕌",
    "오스만 제국 궁정음악의 정수인 터키 마캄 체계를 담고 있습니다. 마캄(선법)·우술(리듬형)·형식(페쉬레브, 사즈세마이시, 쾨체크체 등)에 기반한 즉흥적이고 정교한 음악입니다. 데데 에펜디, 이트리, 칸테미로을루 등 오스만 대가들의 작품 100곡을 선별했습니다.",
    os.path.join(WORLD, "middle_east"),
    "/static/midi/world/middle_east/"
))

# 7. India
regions.append(make_region(
    "india",
    "인도 라가",
    "🇮🇳",
    "인도 고전음악의 근간인 라가(선율형) 체계에 기반한 음악입니다. 바이라브·바게시리·마르와·틸락 카모드 등 다양한 라가의 특성을 담고 있습니다. 힌두스탄(북인도)·카르나틱(남인도) 전통의 즉흥 연주와 탈라(리듬형)의 조화를 경험할 수 있습니다.",
    os.path.join(WORLD, "india"),
    "/static/midi/world/india/"
))

# 8. Asia Traditional (Chinese)
regions.append(make_region(
    "asia_traditional",
    "중국 전통",
    "🇨🇳",
    "중국 전통음악의 대표곡들입니다. 양축 협주곡(梁祝), 춘강화월야(春江花月夜), 이천영월(二泉映月), 고산유수(高山流水) 등 고쟁·얼후·비파·디쯔 등 전통 악기로 연주되는 명곡들을 MIDI로 재현했습니다.",
    os.path.join(WORLD, "asia_traditional"),
    "/static/midi/world/asia_traditional/"
))

# 9. Latin America
regions.append(make_region(
    "latin_america",
    "라틴 아메리카",
    "💃",
    "베네수엘라 호로포·왈츠, 안데스 음악, 라틴 아메리카 전통 음악 모음입니다. 안토니오 라우로의 기타곡, 카바요 비에호(Caballo Viejo), 알마 야네라, 몰리엔도 카페 등 라틴 아메리카의 열정적인 리듬과 선율을 담고 있습니다.",
    os.path.join(WORLD, "latin_america"),
    "/static/midi/world/latin_america/"
))

# 10. National Anthems
regions.append(make_region(
    "national_anthems",
    "세계 국가(國歌)",
    "🏳️",
    "전 세계 국가(國歌)와 애국가 모음입니다. 각 나라의 정체성과 역사를 담은 음악들로, 라 마르세예즈(프랑스), 갓 세이브 더 퀸(영국), 성조기(미국), 독일 연방 찬가, 호주 국가 등을 포함합니다.",
    os.path.join(WORLD, "national_anthems"),
    "/static/midi/world/national_anthems/"
))

total = sum(r["songCount"] for r in regions)

catalog = {
    "totalSongs": total,
    "regions": regions
}

out_path = os.path.join(BASE, "catalog.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

print(f"Generated catalog.json: {total} songs across {len(regions)} regions")
for r in regions:
    print(f"  {r['emoji']} {r['name']}: {r['songCount']} songs")
