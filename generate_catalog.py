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

# 10. National Anthems — properly classified
ANTHEM_COUNTRY_MAP = {
    "la-marseillaise.mid": {"country_en": "France", "country_ko": "프랑스", "title_ko": "라 마르세예즈"},
    "god-save-the-queen.mid": {"country_en": "United Kingdom", "country_ko": "영국", "title_ko": "갓 세이브 더 퀸"},
    "the-star-spangled-banner.mid": {"country_en": "United States", "country_ko": "미국", "title_ko": "성조기"},
    "deutschlandlied.mid": {"country_en": "Germany", "country_ko": "독일", "title_ko": "독일연방찬가"},
    "advance-australia-fair.mid": {"country_en": "Australia", "country_ko": "호주", "title_ko": "아름다운 호주여 전진하라"},
    "het-wilhelmus.mid": {"country_en": "Netherlands", "country_ko": "네덜란드", "title_ko": "빌헬무스"},
    "osterreichische-bundeshymne.mid": {"country_en": "Austria", "country_ko": "오스트리아", "title_ko": "오스트리아 연방찬가"},
    "god-save-the-tsar.mid": {"country_en": "Russia", "country_ko": "러시아", "title_ko": "하느님 차르를 지켜주소서"},
    "land-of-my-fathers.mid": {"country_en": "Wales", "country_ko": "웨일스", "title_ko": "나의 조국의 땅"},
    "scotland-the-brave.mid": {"country_en": "Scotland", "country_ko": "스코틀랜드", "title_ko": "용감한 스코틀랜드"},
    "waltzing-matilda.mid": {"country_en": "Australia", "country_ko": "호주", "title_ko": "왈칭 마틸다"},
    "rule-britannia.mid": {"country_en": "United Kingdom", "country_ko": "영국", "title_ko": "룰 브리타니아"},
    "rule-britannia-flute-and-piano.mid": {"country_en": "United Kingdom", "country_ko": "영국", "title_ko": "룰 브리타니아 (플루트+피아노)"},
    "land-of-hope-and-glory.mid": {"country_en": "United Kingdom", "country_ko": "영국", "title_ko": "희망과 영광의 땅"},
    "hubert-parry-jerusalem.mid": {"country_en": "United Kingdom", "country_ko": "영국", "title_ko": "예루살렘"},
    "i-vow-to-thee-my-country.mid": {"country_en": "United Kingdom", "country_ko": "영국", "title_ko": "나는 그대에게 맹세하리 나의 조국이여"},
    "the-british-grenadiers.mid": {"country_en": "United Kingdom", "country_ko": "영국", "title_ko": "영국 척탄병"},
    "when-johnny-comes-marching-home.mid": {"country_en": "United States", "country_ko": "미국", "title_ko": "조니가 행진해 돌아올 때"},
    "kalinka.mid": {"country_en": "Russia", "country_ko": "러시아", "title_ko": "칼린카"},
    "kalinka-bassoon-and-piano.mid": {"country_en": "Russia", "country_ko": "러시아", "title_ko": "칼린카 (바순+피아노)"},
    "korobeiniki.mid": {"country_en": "Russia", "country_ko": "러시아", "title_ko": "코로베이니키"},
    "the-birch-tree.mid": {"country_en": "Russia", "country_ko": "러시아", "title_ko": "자작나무"},
}

# Sub-groups for national_anthems region
ANTHEM_SUBGROUPS = {
    "국가(國歌)": [
        "la-marseillaise.mid", "god-save-the-queen.mid", "the-star-spangled-banner.mid",
        "deutschlandlied.mid", "advance-australia-fair.mid", "het-wilhelmus.mid",
        "osterreichische-bundeshymne.mid", "god-save-the-tsar.mid",
        "land-of-my-fathers.mid", "scotland-the-brave.mid",
    ],
    "애국가·행진곡": [
        "rule-britannia.mid", "rule-britannia-flute-and-piano.mid",
        "land-of-hope-and-glory.mid", "hubert-parry-jerusalem.mid",
        "i-vow-to-thee-my-country.mid", "the-british-grenadiers.mid",
        "when-johnny-comes-marching-home.mid", "waltzing-matilda.mid",
    ],
    "러시아 민요": [
        "kalinka.mid", "kalinka-bassoon-and-piano.mid", "korobeiniki.mid", "the-birch-tree.mid",
    ],
    "래그타임": [
        "Maple-Leaf-Rag.mid", "Solace.mid", "Swipesy.mid", "The-Chrysanthemum.mid",
        "The-Easy-Winners.mid", "The-Entertainer.mid",
        "scott-joplin-a-breeze-from-alabama.mid", "scott-joplin-and-scott-hayden-sunflower-slow-drag.mid",
        "scott-joplin-bethena-a-concert-waltz.mid", "scott-joplin-elite-syncopations.mid",
        "scott-joplin-peacherine-rag.mid", "scott-joplin-pleasant-moments-ragtime-waltz.mid",
        "scott-joplin-the-cascades.mid", "james-scott-frogs-legs-rag.mid",
        "james-scott-grace-and-beauty-a-classy-rag.mid",
    ],
    "찬송가·성가": [
        "amazing-grace-guitar.mid", "amazing-grace-piano-flute.mid", "amazing-grace-piano.mid",
        "go-tell-it-on-the-mountain-guitar-glenn-jarrett.mid", "go-tell-it-on-the-mountain.mid",
        "morning-has-broken-flute-and-bassoon.mid", "morning-has-broken.mid",
        "swing-low-sweet-chariot.mid",
        "beethoven-symphony9-4-ode-to-joy-piano-solo.mid",
    ],
    "영국 민요·동요": [
        "baa-baa-black-sheep.mid", "bye-baby-bunting.mid",
        "daddy-wouldnt-buy-me-a-bow-wow.mid", "daisy-bell.mid",
        "dont-dilly-dally-on-the-way.mid", "girls-and-boys-come-out-to-play.mid",
        "goosey-goosey-gander.mid", "here-we-go-round-the-mulberry-bush.mid",
        "hey-diddle-diddle.mid", "hickory-dickory-dock.mid", "hot-cross-buns.mid",
        "humpty-dumpty.mid", "if-youre-happy-and-you-know-it.mid",
        "jack-and-jill.mid", "knocked-them-in-the-old-kent-road.mid",
        "lavenders-blue.mid", "lets-all-go-down-the-strand.mid",
        "little-bo-peep.mid", "little-jack-horner.mid", "little-miss-muffet.mid",
        "london-bridge-is-falling-down.mid", "mary-mary-quite-contrary.mid",
        "old-macdonald-had-a-farm.mid", "one-two-three-four-five.mid",
        "polly-perkins-of-paddington-green.mid", "polly-put-the-kettle-on.mid",
        "ride-a-cock-horse.mid", "ring-a-ring-o-roses.mid",
        "rock-a-bye-baby-tune-b.mid", "rub-a-dub-dub.mid",
        "see-saw-margery-daw.mid", "sing-a-song-of-sixpence.mid",
        "ta-ra-ra-boom-de-ay.mid", "ten-green-bottles.mid", "ten-in-the-bed.mid",
        "the-farmers-in-his-den.mid", "the-flying-trapeze.mid",
        "the-grand-old-duke-of-york.mid",
        "the-man-who-broke-the-bank-at-monte-carlo.mid",
        "the-muffin-man.mid", "the-north-wind-doth-blow.mid",
        "the-wheels-on-the-bus.mid", "there-was-a-crooked-man.mid",
        "this-old-man.mid", "three-craws.mid", "tom-tom-the-pipers-son.mid",
        "twinkle-twinkle-little-star.mid", "wee-willie-winkie.mid",
        "i-do-like-to-be-beside-the-seaside.mid",
        "its-a-long-long-way-to-tipperary.mid",
    ],
    "세계 민요": [
        "auld-lang-syne.mid", "auld-lang-syne-guitar.mid",
        "cherry-ripe.mid", "cherry-ripe-piano-solo.mid",
        "drunken-sailor.mid", "early-one-morning.mid", "early-one-morning-oboe-and-piano.mid",
        "flowers-of-the-forest-arranged.mid", "flowers-of-the-forest-original.mid",
        "flowers-of-the-forest-solo.mid", "flowers-of-the-forest.mid",
        "frere-jacques.mid", "frere-jacques-round.mid",
        "greensleeves.mid", "greensleeves-flute-and-guitar.mid", "greensleeves-guitar.mid",
        "johnny-todd.mid", "oh-danny-boy.mid",
        "scarborough-fair.mid", "scarborough-fair-flute-and-piano.mid",
        "spanish-ladies-bassoon-piano.mid", "spanish-ladies-piano.mid",
        "the-skye-boat-song.mid", "wellerman.mid",
        "por-una-cabeza.mid", "por-una-cabeza-piano-solo.mid", "por-una-cabeza-violin-piano.mid",
        "martini-plaisir-d-amour-clarinet-piano.mid", "martini-plaisir-d-amour-piano.mid",
        "martini-plaisir-d-amour-violin-piano.mid",
        "suo-gan-easy-piano.mid", "suo-gan-flute-piano.mid", "suo-gan-piano.mid",
        "fem-far-fire-geder.mid", "fem-far-fire-geder-duet.mid",
        "fem-far-fire-geder-piano-canon.mid", "fem-far-fire-geder-piano-harmony.mid",
    ],
    "중세·르네상스": [
        "seikilos-epitaph.mid",
        "sumer-is-icumen-in.mid", "sumer-is-icumen-in-piano.mid",
        "mirie-it-is-while-sumer-ilast.mid",
        "sellengers-round-arranged.mid", "sellengers-round-virginal.mid",
    ],
}

na_dir = os.path.join(WORLD, "national_anthems")
na_base = "/static/midi/world/national_anthems/"
na_files = set(scan_dir(na_dir))
na_groups = []
classified = set()
for group_name, file_list in ANTHEM_SUBGROUPS.items():
    tracks = []
    for f in file_list:
        if f in na_files:
            t = {"title": title_from_filename(f), "file": f}
            meta = ANTHEM_COUNTRY_MAP.get(f)
            if meta:
                t["country_en"] = meta["country_en"]
                t["country_ko"] = meta["country_ko"]
                if "title_ko" in meta:
                    t["title_ko"] = meta["title_ko"]
            tracks.append(t)
            classified.add(f)
    if tracks:
        na_groups.append({"name": group_name, "tracks": tracks})

# Anything not classified goes to "기타"
remaining = sorted(na_files - classified)
if remaining:
    na_groups.append({"name": "기타", "tracks": make_tracks(remaining)})

na_count = sum(len(g["tracks"]) for g in na_groups)
regions.append({
    "id": "national_anthems",
    "name": "세계 국가(國歌)·민요",
    "emoji": "🏳️",
    "songCount": na_count,
    "description": "전 세계 국가(國歌), 애국가, 민요, 동요, 래그타임 등 다양한 장르의 서양 음악 모음. 나라 이름(한글/영문)으로 검색할 수 있습니다.",
    "basePath": na_base,
    "groups": na_groups
})

total = sum(r["songCount"] for r in regions)

catalog = {
    "totalSongs": total,
    "regions": regions
}

# === Timeline Data (dual-track: Korea vs World) ===
timeline = [
    # World - Ancient
    {"year": -1400, "side": "world", "title": "후리안 찬가", "desc": "현존 최고(最古) 악보 — 시리아 우가릿 출토", "regionId": "ancient_greco_roman", "trackTitle": "Hurrian Hymn No6 1400Bc"},
    {"year": -200, "side": "world", "title": "세이킬로스 비문", "desc": "현존 최고 완전한 악보 (고대 그리스)", "regionId": "national_anthems", "trackTitle": "Seikilos Epitaph"},
    {"year": 138, "side": "world", "title": "아폴론 찬가", "desc": "델피 신전 석판에 새겨진 그리스 음악", "regionId": "ancient_greco_roman", "trackTitle": "Delphic Hymn To Apollo 128Bc"},
    # Korea - Ancient
    {"year": -57, "side": "korea", "title": "삼국시대 시작", "desc": "신라 건국 — 가야금·거문고의 태동", "regionId": "korean", "trackTitle": None},
    {"year": 551, "side": "korea", "title": "가야금 전래", "desc": "가야 우륵이 신라에 가야금 전수", "regionId": "korean", "trackTitle": None},
    {"year": 612, "side": "korea", "title": "미마지의 기악", "desc": "백제 미마지가 일본에 기악(伎樂) 전수", "regionId": "korean", "trackTitle": None},
    # World - Medieval
    {"year": 590, "side": "world", "title": "그레고리안 성가", "desc": "교황 그레고리우스 1세 — 서양 기보법의 시작", "regionId": "europe_medieval", "trackTitle": None},
    {"year": 879, "side": "korea", "title": "처용가", "desc": "신라 헌강왕 때 창작 — 현존 최고 향가", "regionId": "korean", "trackTitle": None},
    {"year": 1000, "side": "world", "title": "귀도 다레초의 기보법", "desc": "4선 악보와 솔미제이션 — 서양 오선보의 기원", "regionId": "europe_medieval", "trackTitle": None},
    {"year": 1100, "side": "world", "title": "트루바두르 음악", "desc": "남프랑스 음유시인의 세속 노래", "regionId": "europe_medieval", "trackTitle": None},
    {"year": 1116, "side": "korea", "title": "대성아악 수입", "desc": "고려, 송나라로부터 아악·악기·악보 전래", "regionId": "korean", "trackTitle": None},
    {"year": 1240, "side": "world", "title": "여름이 오면 (Sumer Is Icumen In)", "desc": "현존 최고 영어 라운드 — 다성음악의 시작", "regionId": "national_anthems", "trackTitle": "Sumer Is Icumen In"},
    {"year": 1300, "side": "world", "title": "아르스 노바", "desc": "기욤 드 마쇼 — 복잡한 리듬과 다성음악의 혁신", "regionId": "europe_medieval", "trackTitle": None},
    # Korea - Joseon
    {"year": 1392, "side": "korea", "title": "조선 건국", "desc": "아악 정비, 궁중음악 체계화 시작", "regionId": "korean", "trackTitle": None},
    {"year": 1430, "side": "korea", "title": "박연의 아악 정비", "desc": "편경 제작, 율관 교정 — 조선 아악의 완성", "regionId": "korean", "trackTitle": None},
    {"year": 1447, "side": "korea", "title": "정간보 창제 ★", "desc": "세종대왕 — 동양 최초 정량기보법. 서양 오선보보다 200년 앞서", "regionId": "korean", "trackTitle": "여민락"},
    {"year": 1450, "side": "korea", "title": "보태평·정대업", "desc": "세종대왕 작곡 → 종묘제례악 (유네스코 2001)", "regionId": "korean", "trackTitle": "영산회상 상령산"},
    {"year": 1450, "side": "world", "title": "르네상스 음악", "desc": "뒤파이·오케겜 — 합창 다성음악의 황금기", "regionId": "europe_medieval", "trackTitle": None},
    {"year": 1493, "side": "korea", "title": "악학궤범", "desc": "성현 편찬 — 한국 최초의 종합 악서", "regionId": "korean", "trackTitle": None},
    {"year": 1500, "side": "world", "title": "오스만 궁정음악", "desc": "마캄 체계 확립 — 중동 음악의 정수", "regionId": "middle_east", "trackTitle": None},
    {"year": 1580, "side": "world", "title": "그린슬리브스", "desc": "영국 르네상스 민요의 대표작", "regionId": "national_anthems", "trackTitle": "Greensleeves"},
    {"year": 1600, "side": "korea", "title": "가곡의 발전", "desc": "조선 문인들의 풍류방 음악 — 시조+노래", "regionId": "korean", "trackTitle": None},
    {"year": 1600, "side": "world", "title": "바로크 시대 시작", "desc": "오페라 탄생, 통주저음 — 몬테베르디", "regionId": "europe_medieval", "trackTitle": None},
    {"year": 1700, "side": "world", "title": "인도 라가의 체계화", "desc": "힌두스탄·카르나틱 고전음악 분화", "regionId": "india", "trackTitle": None},
    {"year": 1750, "side": "korea", "title": "판소리 탄생", "desc": "민중 속에서 탄생한 서사적 음악극 (유네스코 2003)", "regionId": "korean", "trackTitle": None},
    {"year": 1760, "side": "world", "title": "아일랜드 민요의 황금기", "desc": "캐롤런 — 하프 음악의 수집과 보존", "regionId": "celtic", "trackTitle": None},
    {"year": 1792, "side": "world", "title": "라 마르세예즈", "desc": "프랑스 혁명의 국가 — 루제 드 릴 작곡", "regionId": "national_anthems", "trackTitle": "La Marseillaise"},
    {"year": 1800, "side": "korea", "title": "산조의 탄생", "desc": "김창조 — 가야금산조 창시. 즉흥 기악 독주의 꽃", "regionId": "korean", "trackTitle": None},
    {"year": 1814, "side": "world", "title": "성조기 (The Star-Spangled Banner)", "desc": "미국 국가 — 프랜시스 스콧 키 작사", "regionId": "national_anthems", "trackTitle": "The Star Spangled Banner"},
    {"year": 1833, "side": "world", "title": "독일연방찬가 (Deutschlandlied)", "desc": "하이든 선율 + 호프만 가사", "regionId": "national_anthems", "trackTitle": "Deutschlandlied"},
    {"year": 1840, "side": "world", "title": "어메이징 그레이스", "desc": "존 뉴턴의 찬송가 — 세계에서 가장 유명한 성가", "regionId": "national_anthems", "trackTitle": "Amazing Grace Piano"},
    {"year": 1850, "side": "world", "title": "갓 세이브 더 퀸", "desc": "영국 국가 — 세계 최고(最古) 국가 중 하나", "regionId": "national_anthems", "trackTitle": "God Save The Queen"},
    {"year": 1860, "side": "world", "title": "중국 전통음악의 정립", "desc": "고산유수·이천영월 — 고쟁·얼후의 대표곡", "regionId": "asia_traditional", "trackTitle": None},
    {"year": 1870, "side": "korea", "title": "영산회상의 완성", "desc": "현악영산회상 9곡 모음곡 — 풍류의 정수", "regionId": "korean", "trackTitle": "영산회상 상령산"},
    {"year": 1880, "side": "world", "title": "라틴 아메리카 음악", "desc": "호로포·왈츠·탱고 — 라틴 리듬의 확산", "regionId": "latin_america", "trackTitle": None},
    {"year": 1899, "side": "world", "title": "래그타임 혁명", "desc": "스콧 조플린 'Maple Leaf Rag' — 미국 대중음악의 시작", "regionId": "national_anthems", "trackTitle": "Maple Leaf Rag"},
    {"year": 1902, "side": "korea", "title": "애국가 작곡", "desc": "안익태 작곡 — 대한민국 국가", "regionId": "korean", "trackTitle": None},
    {"year": 1950, "side": "korea", "title": "국립국악원 설립", "desc": "한국 전통음악 보존·연구·공연의 중심 기관", "regionId": "korean", "trackTitle": None},
    {"year": 2001, "side": "korea", "title": "종묘제례악 유네스코 등재", "desc": "세종대왕의 보태평·정대업 — 인류무형문화유산", "regionId": "korean", "trackTitle": None},
    {"year": 2003, "side": "korea", "title": "판소리 유네스코 등재", "desc": "인류무형문화유산 — 세계가 인정한 한국 음악극", "regionId": "korean", "trackTitle": None},
]

catalog["timeline"] = timeline

out_path = os.path.join(BASE, "catalog.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

print(f"Generated catalog.json: {total} songs across {len(regions)} regions")
for r in regions:
    print(f"  {r['emoji']} {r['name']}: {r['songCount']} songs")
