#!/usr/bin/env python3
"""
Enrich catalog.json with composer, year, era, tags for all 748 tracks.
Run: python3 scripts/enrich_catalog.py
"""
import json, re, os

CATALOG = os.path.join(os.path.dirname(__file__), '..', 'catalog.json')

# ─── Korean Traditional Music ─────────────────────────────
KOREAN_META = {
    "영산회상": {"composer": "전통 (작자 미상)", "year": 1500, "era": "조선 초기~후기", "tags": ["정악", "풍류", "합주"]},
    "관악영산회상": {"composer": "전통 (작자 미상)", "year": 1700, "era": "조선 후기", "tags": ["정악", "관악", "합주"]},
    "평조회상": {"composer": "전통 (작자 미상)", "year": 1700, "era": "조선 후기", "tags": ["정악", "풍류", "평조"]},
    "수제천": {"composer": "전통 (백제 유래)", "year": 600, "era": "백제~조선", "tags": ["정악", "관악", "무형문화재"]},
    "여민락": {"composer": "세종대왕 (1397~1450)", "year": 1445, "era": "조선 전기", "tags": ["정악", "세종", "궁중"]},
    "보허자": {"composer": "전통 (송나라 전래)", "year": 1100, "era": "고려", "tags": ["정악", "당악", "관현"]},
    "취타": {"composer": "전통 (작자 미상)", "year": 1600, "era": "조선", "tags": ["정악", "군악", "행진"]},
    "남창우조": {"composer": "전통 가객 (이세춘 등)", "year": 1750, "era": "조선 후기", "tags": ["가곡", "남창", "우조"]},
    "남창계면": {"composer": "전통 가객 (이세춘 등)", "year": 1750, "era": "조선 후기", "tags": ["가곡", "남창", "계면조"]},
    "여창우조": {"composer": "전통 (기녀 연행)", "year": 1750, "era": "조선 후기", "tags": ["가곡", "여창", "우조"]},
    "여창계면": {"composer": "전통 (기녀 연행)", "year": 1750, "era": "조선 후기", "tags": ["가곡", "여창", "계면조"]},
    "여창반우반계": {"composer": "전통", "year": 1750, "era": "조선 후기", "tags": ["가곡", "여창", "반우반계"]},
    "천년만세": {"composer": "전통 (작자 미상)", "year": 1800, "era": "조선 후기", "tags": ["정악", "풍류", "기악"]},
    "도드리": {"composer": "전통 (작자 미상)", "year": 1700, "era": "조선 후기", "tags": ["정악", "기악", "변주"]},
    "자진한잎": {"composer": "전통 (작자 미상)", "year": 1800, "era": "조선 후기", "tags": ["정악", "풍류"]},
    "현악취타": {"composer": "전통 (작자 미상)", "year": 1600, "era": "조선", "tags": ["정악", "군악", "현악"]},
}

# ─── Ancient Greco-Roman ─────────────────────────────────
ANCIENT_META = {
    "hurrian": {"composer": "작자 미상 (고대 시리아)", "year": -1400, "era": "청동기 시대", "tags": ["고대", "수메르", "찬가"]},
    "seikilos": {"composer": "세이킬로스 (Seikilos)", "year": -200, "era": "헬레니즘", "tags": ["고대 그리스", "묘비", "세계최고악곡"]},
    "delphic": {"composer": "아테나이오스 (Athenaios) / 리메니오스 (Limenius)", "year": -128, "era": "헬레니즘", "tags": ["고대 그리스", "신전", "아폴론"]},
    "mesomedes_helios": {"composer": "메소메데스 (Mesomedes, 2세기)", "year": 130, "era": "로마 제국", "tags": ["로마", "궁정", "찬가"]},
    "mesomedes_muse": {"composer": "메소메데스 (Mesomedes, 2세기)", "year": 130, "era": "로마 제국", "tags": ["로마", "궁정", "뮤즈"]},
    "mesomedes_nemesis": {"composer": "메소메데스 (Mesomedes, 2세기)", "year": 130, "era": "로마 제국", "tags": ["로마", "궁정", "복수의 여신"]},
    "orestes": {"composer": "에우리피데스 (Euripides, BC 480~406)", "year": -200, "era": "고전기", "tags": ["고대 그리스", "비극", "코러스"]},
    "byzantine": {"composer": "전통 (비잔틴 교회)", "year": 600, "era": "비잔틴", "tags": ["비잔틴", "성가", "기독교"]},
    "egyptian": {"composer": "복원 (현대 학자)", "year": -1500, "era": "고대 이집트", "tags": ["이집트", "복원", "찬가"]},
    "gregorian_dies_irae": {"composer": "전통 (교회)", "year": 1250, "era": "중세", "tags": ["그레고리안", "성가", "진노의 날"]},
    "istanpitta": {"composer": "작자 미상", "year": 1350, "era": "중세 이탈리아", "tags": ["무곡", "에스탐피", "이탈리아"]},
    "roman_water_organ": {"composer": "복원 (현대 학자)", "year": 100, "era": "로마 제국", "tags": ["로마", "수력 오르간", "복원"]},
    "bellermann": {"composer": "작자 미상 (벨레르만 익명)", "year": 150, "era": "로마 제국", "tags": ["고대 그리스", "익명", "교육용"]},
    "sappho": {"composer": "복원 (사포 시 기반)", "year": -600, "era": "고졸기", "tags": ["고대 그리스", "서정시", "복원"]},
    "pythag": {"composer": "복원 (피타고라스 음계)", "year": -500, "era": "고졸기", "tags": ["고대 그리스", "음계이론", "복원"]},
}

# ─── Turkish Makam — parse from filename ─────────────────
def parse_turkish(filename):
    """Parse: makam--form--usul--title--composer.mid"""
    stem = filename.replace('.mid', '')
    parts = stem.split('--')
    makam = parts[0] if len(parts) > 0 else "?"
    form = parts[1] if len(parts) > 1 else ""
    usul = parts[2] if len(parts) > 2 else ""
    title = parts[3].replace('_', ' ') if len(parts) > 3 else ""
    composer = parts[4].replace('_', ' ') if len(parts) > 4 else "작자 미상"
    
    form_kr = {
        "ilahi": "일라히 (종교 찬가)", "pesrev": "페쉬레브 (기악 전주곡)",
        "seyir": "쉐이르 (마캄 진행 시범)", "sarki": "샤르크 (노래)",
        "kupe": "퀴페", "aranagme": "아라나메", "agirsemai": "아으르세마이",
        "selam": "셀람", "yuruksemai": "유뤽세마이",
        "sazsemai": "사즈세마이 (기악곡)",
    }.get(form, form)
    
    return {
        "composer": composer.title() if composer != "작자 미상" else "작자 미상 (오스만 궁정)",
        "year": 1600,
        "era": "오스만 제국 (16~19세기)",
        "tags": ["마캄", makam, form] + ([usul] if usul else []),
        "makam": makam,
        "form": form_kr,
    }

# ─── Medieval/Renaissance — pattern matching ─────────────
MEDIEVAL_COMPOSERS = {
    "clark": {"composer": "Clark (현대 편곡)", "tags": ["편곡", "중세"]},
    "machaut": {"composer": "기욤 드 마쇼 (Guillaume de Machaut, 1300~1377)", "tags": ["아르스 노바", "프랑스"]},
    "landini": {"composer": "프란체스코 란디니 (Francesco Landini, 1325~1397)", "tags": ["트레첸토", "이탈리아"]},
    "dufay": {"composer": "기욤 뒤파이 (Guillaume Dufay, 1397~1474)", "tags": ["부르고뉴 악파"]},
    "josquin": {"composer": "조스캥 데 프레 (Josquin des Prez, 1450~1521)", "tags": ["르네상스", "플랑드르"]},
    "palestrina": {"composer": "팔레스트리나 (Palestrina, 1525~1594)", "tags": ["르네상스", "대위법"]},
    "byrd": {"composer": "윌리엄 버드 (William Byrd, 1543~1623)", "tags": ["르네상스", "영국"]},
    "dowland": {"composer": "존 다울랜드 (John Dowland, 1563~1626)", "tags": ["르네상스", "류트"]},
    "morley": {"composer": "토마스 몰리 (Thomas Morley, 1557~1602)", "tags": ["르네상스", "영국"]},
    "tallis": {"composer": "토마스 탈리스 (Thomas Tallis, 1505~1585)", "tags": ["르네상스", "영국"]},
    "bellugi": {"composer": "Bellugi (현대 복원 편곡)", "tags": ["복원", "편곡"]},
    "cantigas": {"composer": "알폰소 10세 (Alfonso X, 1221~1284)", "tags": ["칸티가", "스페인"]},
    "hildegard": {"composer": "힐데가르트 폰 빙엔 (Hildegard von Bingen, 1098~1179)", "tags": ["수녀", "독일"]},
    "estampie": {"composer": "작자 미상 (13세기)", "tags": ["무곡", "에스탐피"]},
    "saltarello": {"composer": "작자 미상 (14세기)", "tags": ["무곡", "이탈리아"]},
    "trotto": {"composer": "작자 미상 (14세기)", "tags": ["무곡", "이탈리아"]},
    "sumer": {"composer": "작자 미상 (1240, 레딩 수도원)", "tags": ["라운드", "영국", "최초"]},
    "greensleeves": {"composer": "작자 미상 (16세기 영국)", "tags": ["민요", "영국"]},
}

MEDIEVAL_ERAS = {
    "clark": ("중세~르네상스 (복원)", 1300),
    "bellugi": ("중세~르네상스 (복원)", 1400),
    "machaut": ("아르스 노바 (14세기)", 1350),
    "landini": ("트레첸토 (14세기)", 1370),
    "dufay": ("르네상스 초기 (15세기)", 1430),
    "josquin": ("르네상스 (15세기)", 1490),
    "palestrina": ("르네상스 후기 (16세기)", 1560),
    "byrd": ("르네상스 후기 (16세기)", 1580),
    "dowland": ("르네상스 후기 (16세기)", 1595),
    "cantigas": ("중세 (13세기)", 1270),
    "hildegard": ("중세 (12세기)", 1150),
    "estampie": ("중세 (13세기)", 1280),
    "saltarello": ("중세 (14세기)", 1350),
    "trotto": ("중세 (14세기)", 1300),
    "sumer": ("중세 (13세기)", 1240),
    "greensleeves": ("르네상스 (16세기)", 1580),
}

# ─── National Anthems ────────────────────────────────────
ANTHEM_META = {
    "la-marseillaise": {"composer": "클로드 조제프 루제 드 릴 (1760~1836)", "year": 1792, "country": "프랑스", "tags": ["국가", "프랑스 혁명"]},
    "god-save": {"composer": "작자 미상 (전통)", "year": 1745, "country": "영국", "tags": ["국가", "영국"]},
    "star-spangled": {"composer": "존 스태포드 스미스 (1750~1836)", "year": 1814, "country": "미국", "tags": ["국가", "미국"]},
    "deutschlandlied": {"composer": "요제프 하이든 (1732~1809)", "year": 1797, "country": "독일", "tags": ["국가", "독일"]},
    "amazing-grace": {"composer": "전통 선율 / 존 뉴턴 (작사, 1725~1807)", "year": 1779, "country": "영국/미국", "tags": ["찬송가", "복음"]},
    "rule-britannia": {"composer": "토마스 아른 (Thomas Arne, 1710~1778)", "year": 1740, "country": "영국", "tags": ["애국가", "영국"]},
    "advance-australia": {"composer": "피터 도즈 맥코믹 (1834~1916)", "year": 1878, "country": "호주", "tags": ["국가", "호주"]},
    "maple-leaf-rag": {"composer": "스콧 조플린 (Scott Joplin, 1868~1917)", "year": 1899, "country": "미국", "tags": ["래그타임", "피아노"]},
    "entertainer": {"composer": "스콧 조플린 (Scott Joplin, 1868~1917)", "year": 1902, "country": "미국", "tags": ["래그타임", "피아노"]},
    "solace": {"composer": "스콧 조플린 (Scott Joplin, 1868~1917)", "year": 1909, "country": "미국", "tags": ["래그타임", "피아노"]},
    "swipesy": {"composer": "스콧 조플린 & 아서 마셜", "year": 1900, "country": "미국", "tags": ["래그타임"]},
    "chrysanthemum": {"composer": "스콧 조플린 (Scott Joplin, 1868~1917)", "year": 1904, "country": "미국", "tags": ["래그타임"]},
    "easy-winners": {"composer": "스콧 조플린 (Scott Joplin, 1868~1917)", "year": 1901, "country": "미국", "tags": ["래그타임"]},
    "land-of-hope": {"composer": "에드워드 엘가 (Edward Elgar, 1857~1934)", "year": 1901, "country": "영국", "tags": ["행진곡", "영국"]},
    "danny-boy": {"composer": "프레더릭 웨더리 (작사) / 전통 선율", "year": 1913, "country": "아일랜드", "tags": ["민요", "아일랜드"]},
    "greensleeves": {"composer": "작자 미상 (16세기)", "year": 1580, "country": "영국", "tags": ["민요", "영국"]},
    "auld-lang-syne": {"composer": "로버트 번즈 (작사) / 전통 선율", "year": 1788, "country": "스코틀랜드", "tags": ["민요", "송년"]},
    "hatikvah": {"composer": "사무엘 코헨 (1870~1940)", "year": 1888, "country": "이스라엘", "tags": ["국가", "이스라엘"]},
    "kimigayo": {"composer": "하야시 히로모리 / 에케르트 편곡", "year": 1880, "country": "일본", "tags": ["국가", "일본"]},
}

# ─── Celtic ──────────────────────────────────────────────
CELTIC_META = {
    "afton": {"composer": "알렉산더 하운스 (곡) / 로버트 번즈 (시)", "year": 1791, "tags": ["스코틀랜드", "번즈"]},
    "amgrace": {"composer": "전통 / 존 뉴턴 (작사)", "year": 1779, "tags": ["아일랜드", "찬송가"]},
    "auldlang": {"composer": "전통 / 로버트 번즈 (작사, 1788)", "year": 1788, "tags": ["스코틀랜드", "송년"]},
    "danny": {"composer": "전통 (Londonderry Air) / 웨더리 (작사)", "year": 1913, "tags": ["아일랜드"]},
    "bonidoon": {"composer": "전통 / 로버트 번즈", "year": 1791, "tags": ["스코틀랜드", "번즈"]},
    "loch": {"composer": "전통 (스코틀랜드)", "year": 1870, "tags": ["스코틀랜드", "호수"]},
    "bluebonn": {"composer": "전통 (스코틀랜드)", "year": 1700, "tags": ["스코틀랜드", "야코바이트"]},
    "carolan": {"composer": "투를로흐 오캐롤란 (1670~1738)", "year": 1710, "tags": ["아일랜드", "하프"]},
}

# ─── India ───────────────────────────────────────────────
INDIA_META = {
    "Adana": "아다나", "Alhiya Bilawal": "알히야 빌라왈", "Bageshri": "바게쉬리",
    "Bahar": "바하르", "Bazigar": "바지가르", "Behag": "베하그",
    "Bhairav": "바이라브", "Bhatiyar": "바티야르", "Bhimpalasi": "빔팔라시",
    "Bhupali": "부팔리", "Bilawal": "빌라왈", "Charukeshi": "차루케쉬",
    "Darbari Kanada": "다르바리 카나다", "Des": "데스", "Desh": "데쉬",
    "Durga": "두르가", "Hamir": "하미르", "Jaunpuri": "자운푸리",
    "Kafi": "카피", "Kedar": "케다르",
}

# ─── China ───────────────────────────────────────────────
CHINA_META = {
    "Butterfly_Lovers": {"title_ko": "양축 (梁祝) — 나비의 연인", "composer": "허잔쥔·천강 (何占豪·陈钢, 1959)", "year": 1959, "tags": ["바이올린 협주곡", "중국"]},
    "Chun_Jiang_Hua_Yue_Yie": {"title_ko": "춘강화월야 (春江花月夜)", "composer": "전통 (당나라 유래)", "year": 800, "tags": ["비파", "당시"]},
    "Er_Quan_Yang_Yue": {"title_ko": "이천영월 (二泉映月)", "composer": "아빙 (阿炳, 1893~1950)", "year": 1950, "tags": ["얼후", "무석"]},
    "Erta_Hema": {"title_ko": "얼타이하마", "composer": "전통 (몽골)", "year": 1800, "tags": ["몽골", "초원"]},
    "Erta_Hema_2": {"title_ko": "얼타이하마 2", "composer": "전통 (몽골)", "year": 1800, "tags": ["몽골"]},
    "Gao_Shan_Liu_Shui": {"title_ko": "고산유수 (高山流水)", "composer": "전통 (춘추시대 유래)", "year": -500, "tags": ["고쟁", "백아"]},
    "Jian_He": {"title_ko": "전하 (剑河)", "composer": "현대", "year": 1980, "tags": ["현대"]},
    "Liu_Yang_He": {"title_ko": "류양하 (浏阳河)", "composer": "당벽광 (唐璧光, 1951)", "year": 1951, "tags": ["민요", "호남"]},
    "Mei_Hua_San_Nong": {"title_ko": "매화삼농 (梅花三弄)", "composer": "환이 (桓伊, 4세기)", "year": 350, "tags": ["고금", "매화"]},
    "Mo_Li_Hua": {"title_ko": "모리화 (茉莉花) — 재스민", "composer": "전통 (청나라)", "year": 1800, "tags": ["민요", "강소"]},
    "Mu_Yang_Gu_Shi": {"title_ko": "목양고사 (牧羊姑事)", "composer": "전통", "year": 1900, "tags": ["민요"]},
    "Su_Wu_Mu_Yang": {"title_ko": "소무목양 (蘇武牧羊)", "composer": "전통 (한나라 유래)", "year": -100, "tags": ["한나라", "역사"]},
    "Tai_Hu_Chuan": {"title_ko": "태호선 (太湖船)", "composer": "전통 (강소)", "year": 1800, "tags": ["민요", "호수"]},
}

# ─── Latin America ───────────────────────────────────────
LATIN_KNOWN = {
    "AlmaLlanera": {"title_ko": "야네라의 영혼", "composer": "페드로 엘리아스 구티에레스 (1870~1954)", "year": 1914, "country": "베네수엘라"},
    "MoliendoCafe": {"title_ko": "커피를 갈며", "composer": "우고 블랑코 (Hugo Blanco, 1940~)", "year": 1961, "country": "베네수엘라"},
    "Mananitapueblerina": {"title_ko": "시골 아침", "composer": "전통 (멕시코)", "year": 1900, "country": "멕시코"},
}

# ═══ Main Enrichment Logic ═══════════════════════════════
def enrich():
    with open(CATALOG) as f:
        cat = json.load(f)
    
    enriched = 0
    
    for region in cat["regions"]:
        rid = region["id"]
        
        for group in region.get("groups", []):
            for track in group.get("tracks", []):
                fn = track["file"]
                fn_lower = fn.lower()
                stem = fn.replace('.mid', '').replace('.midi', '')
                
                # ── Korean ──
                if rid == "korean":
                    for key, meta in KOREAN_META.items():
                        if key in fn:
                            track.update(meta)
                            enriched += 1
                            break
                    else:
                        track.setdefault("composer", "전통 (작자 미상)")
                        track.setdefault("year", 1600)
                        track.setdefault("era", "조선")
                        track.setdefault("tags", ["정악"])
                        enriched += 1
                
                # ── Ancient ──
                elif rid == "ancient_greco_roman":
                    matched = False
                    for key, meta in ANCIENT_META.items():
                        if key in fn_lower:
                            track.update(meta)
                            enriched += 1
                            matched = True
                            break
                    if not matched:
                        track.setdefault("composer", "작자 미상 (고대)")
                        track.setdefault("year", -100)
                        track.setdefault("era", "고대")
                        track.setdefault("tags", ["고대"])
                        enriched += 1
                
                # ── Medieval ──
                elif rid == "europe_medieval":
                    matched = False
                    for key, meta in MEDIEVAL_COMPOSERS.items():
                        if key in fn_lower:
                            track["composer"] = meta["composer"]
                            track["tags"] = meta["tags"] + ["중세·르네상스"]
                            era_info = MEDIEVAL_ERAS.get(key, ("중세~르네상스", 1350))
                            track["era"] = era_info[0]
                            track["year"] = era_info[1]
                            enriched += 1
                            matched = True
                            break
                    if not matched:
                        track.setdefault("composer", "작자 미상")
                        track.setdefault("year", 1350)
                        track.setdefault("era", "중세~르네상스")
                        track.setdefault("tags", ["중세"])
                        enriched += 1
                
                # ── Turkish ──
                elif rid == "middle_east":
                    meta = parse_turkish(fn)
                    track.update(meta)
                    enriched += 1
                
                # ── Celtic ──
                elif rid == "celtic":
                    matched = False
                    for key, meta in CELTIC_META.items():
                        if key in fn_lower:
                            track.update(meta)
                            track.setdefault("era", "16~19세기")
                            track.setdefault("composer", meta.get("composer", "전통"))
                            enriched += 1
                            matched = True
                            break
                    if not matched:
                        track.setdefault("composer", "전통 (켈틱)")
                        track.setdefault("year", 1750)
                        track.setdefault("era", "16~19세기")
                        track.setdefault("tags", ["켈틱", "전통"])
                        enriched += 1
                
                # ── India ──
                elif rid == "india":
                    raga_name = stem.replace('_', ' ')
                    raga_kr = INDIA_META.get(raga_name, raga_name)
                    track["composer"] = "전통 (힌두스탄)"
                    track["year"] = 1700
                    track["era"] = "무굴 제국~현대"
                    track["tags"] = ["라가", "인도", "힌두스탄"]
                    track["title_ko"] = f"라가 {raga_kr}" if isinstance(raga_kr, str) else raga_kr
                    enriched += 1
                
                # ── China ──
                elif rid == "asia_traditional":
                    meta = CHINA_META.get(stem)
                    if meta:
                        track.update(meta)
                    else:
                        track.setdefault("composer", "전통 (중국)")
                        track.setdefault("year", 1800)
                        track.setdefault("era", "명·청")
                        track.setdefault("tags", ["중국", "전통"])
                    enriched += 1
                
                # ── Latin America ──
                elif rid == "latin_america":
                    meta = LATIN_KNOWN.get(stem)
                    if meta:
                        track.update(meta)
                    else:
                        track.setdefault("composer", "전통 (라틴 아메리카)")
                        track.setdefault("year", 1850)
                        track.setdefault("era", "19~20세기")
                        track.setdefault("tags", ["라틴", "전통"])
                    enriched += 1
                
                # ── National Anthems ──
                elif rid == "national_anthems":
                    matched = False
                    for key, meta in ANTHEM_META.items():
                        if key in fn_lower:
                            track.update(meta)
                            track.setdefault("era", "18~20세기")
                            enriched += 1
                            matched = True
                            break
                    if not matched:
                        track.setdefault("composer", "작자 미상")
                        track.setdefault("year", 1900)
                        track.setdefault("era", "19~20세기")
                        track.setdefault("tags", ["국가"])
                        enriched += 1
                
                # ── Fallback ──
                else:
                    track.setdefault("composer", "작자 미상")
                    track.setdefault("year", 1800)
                    track.setdefault("tags", [])
                    enriched += 1
    
    with open(CATALOG, 'w', encoding='utf-8') as f:
        json.dump(cat, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {enriched}곡 메타데이터 부착 완료")
    
    # Verify
    total = has_composer = has_year = has_tags = 0
    for r in cat["regions"]:
        for g in r.get("groups", []):
            for t in g.get("tracks", []):
                total += 1
                if t.get("composer"): has_composer += 1
                if t.get("year"): has_year += 1
                if t.get("tags"): has_tags += 1
    
    print(f"   composer: {has_composer}/{total}")
    print(f"   year: {has_year}/{total}")
    print(f"   tags: {has_tags}/{total}")

if __name__ == "__main__":
    enrich()
