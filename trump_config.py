# -*- coding: utf-8 -*-
"""
트럼프 임팩트 트래커 설정
- 트럼프 언급 감지 키워드
- 정책/산업 토픽 분류 사전
- 토픽별 한국 관련주 매핑
- 추가 RSS 피드 (영문/공시)

기존 config.py 와 별도 파일로 운영하면 유지보수가 쉽습니다.
관련주 목록은 시점에 따라 바뀌므로 정기적으로 점검하세요.
"""

# ---------------------------------------------------------------
# 1. 트럼프 언급 감지 키워드
# ---------------------------------------------------------------
# 뉴스 제목/본문에 아래 키워드 중 하나라도 있으면 "트럼프 관련"으로 분류
TRUMP_KEYWORDS = [
    "트럼프",
    "Trump",
    "트럼프 행정부",
    "트럼프 정부",
    "트럼프 대통령",
    "Trump administration",
    "백악관",
    "White House",
    "MAGA",
    "USTR",
    "美 행정부",
    "미 행정부",
]


# ---------------------------------------------------------------
# 2. 토픽 분류 사전
# ---------------------------------------------------------------
# 트럼프 관련 뉴스를 추가로 어떤 정책/산업 토픽인지 분류
# 각 토픽: {키워드 리스트, 아이콘, 설명}
# 키워드는 대소문자 구분 없이 부분 일치로 매칭
TRUMP_TOPICS = {
    "양자컴퓨터": {
        "icon": "⚛",
        "keywords": [
            "양자컴퓨터", "양자컴퓨팅", "양자 컴퓨팅", "Quantum",
            "양자 칩", "양자칩", "양자암호", "양자 암호", "큐비트",
            "IonQ", "아이온큐", "리게티", "Rigetti", "D-Wave",
            "디웨이브", "IQM", "퀀텀", "양자 산업",
        ],
        "description": "트럼프 행정부가 양자컴퓨팅 기업 지분 직접 확보 추진",
    },
    "관세/무역": {
        "icon": "⚖",
        "keywords": [
            "관세", "Tariff", "tariff", "상호관세", "보복관세",
            "무역전쟁", "통상", "301조", "232조", "FTA",
            "무역대표부", "USTR", "수출규제", "무역법",
        ],
        "description": "관세 부과·무역 협상이 한국 수출 산업에 미치는 영향",
    },
    "반도체": {
        "icon": "▣",
        "keywords": [
            "반도체", "Chip", "chip", "semiconductor",
            "HBM", "메모리", "파운드리", "TSMC", "인텔",
            "Intel", "마이크론", "Micron", "엔비디아", "Nvidia",
            "반도체 관세", "칩스법", "CHIPS Act",
        ],
        "description": "반도체 관세·보조금·지분 확보 정책 동향",
    },
    "자동차": {
        "icon": "▤",
        "keywords": [
            "자동차 관세", "전기차 보조금", "IRA",
            "Inflation Reduction Act", "리쇼어링",
            "현대차 미국", "기아 미국", "테슬라",
        ],
        "description": "자동차 관세 25→15% 인하, IRA 보조금 변화",
    },
    "조선": {
        "icon": "▣",
        "keywords": [
            "MASGA", "조선업 협력", "美 조선",
            "조선 동맹", "쇄빙선", "함정 건조",
            "Jones Act", "존스법",
        ],
        "description": "한미 조선업 협력(MASGA) 본격화",
    },
    "원자력/에너지": {
        "icon": "☢",
        "keywords": [
            "원전 수출", "SMR", "소형원자로",
            "LNG", "셰일가스", "에너지 동맹",
            "원자력 협력", "넷제로", "탄소중립",
        ],
        "description": "한미 원자력 협력·LNG 1000억달러 구매 약속",
    },
    "방산/우주": {
        "icon": "✦",
        "keywords": [
            "방산", "K-방산", "무기 수출",
            "우주개발", "Space Force", "스페이스X",
            "Starlink", "스타링크", "위성",
        ],
        "description": "방산·우주산업에서의 한미 협력 확대",
    },
    "암호화폐": {
        "icon": "₿",
        "keywords": [
            "비트코인", "Bitcoin", "이더리움", "Ethereum",
            "암호화폐", "가상자산", "스테이블코인",
            "디지털 자산", "암호화폐 규제", "SEC",
        ],
        "description": "트럼프의 친크립토 정책과 한국 가상자산 시장",
    },
    "AI/빅테크": {
        "icon": "◉",
        "keywords": [
            "AI 행정명령", "AI Executive Order",
            "OpenAI", "메타", "Meta", "구글", "Google",
            "AI 규제", "AI 패권",
        ],
        "description": "AI 행정명령·빅테크 규제 동향",
    },
    "중국 견제": {
        "icon": "▲",
        "keywords": [
            "中 견제", "중국 견제", "디커플링", "Decoupling",
            "탈중국", "중국 제재", "수출 통제",
            "Entity List", "엔티티 리스트",
        ],
        "description": "對중국 견제와 한국 기업 공급망 영향",
    },
}


# ---------------------------------------------------------------
# 3. 토픽별 한국 관련주 매핑
# ---------------------------------------------------------------
# 시장에서 통상 "관련주"로 묶이는 한국 상장 종목들
# 주의: 단순 테마 매핑이며 실제 사업 연관성/펀더멘털과 별개입니다.
# 버핏식 관점에서는 반드시 재무제표·해자 확인 후 판단하세요.
TOPIC_STOCKS = {
    "양자컴퓨터": [
        {"name": "한국첨단소재", "code": "031980", "market": "KOSDAQ",
         "note": "초전도·절연·패키징 소재, IQM 협력 기대"},
        {"name": "케이씨에스",   "code": "115500", "market": "KOSDAQ",
         "note": "양자암호 칩, 금융 인프라 보안"},
        {"name": "엑스게이트",   "code": "356680", "market": "KOSDAQ",
         "note": "양자 보안 게이트웨이"},
        {"name": "드림시큐리티", "code": "203650", "market": "KOSDAQ",
         "note": "양자암호 기반 보안 솔루션"},
        {"name": "아이씨티케이", "code": "456010", "market": "KOSDAQ",
         "note": "PUF 기반 양자 보안"},
        {"name": "쏠리드",       "code": "050890", "market": "KOSDAQ",
         "note": "양자 통신 인프라"},
    ],
    "관세/무역": [
        {"name": "삼성전자",   "code": "005930", "market": "KOSPI",
         "note": "반도체 대미 수출 직접 영향"},
        {"name": "SK하이닉스", "code": "000660", "market": "KOSPI",
         "note": "HBM·메모리 대미 수출"},
        {"name": "현대차",     "code": "005380", "market": "KOSPI",
         "note": "자동차 관세 25→15%, 미국 현지 투자"},
        {"name": "기아",       "code": "000270", "market": "KOSPI",
         "note": "자동차 관세 영향"},
        {"name": "포스코홀딩스", "code": "005490", "market": "KOSPI",
         "note": "철강 232조 관세 영향"},
    ],
    "반도체": [
        {"name": "삼성전자",     "code": "005930", "market": "KOSPI",
         "note": "테일러 파운드리 2026 양산"},
        {"name": "SK하이닉스",   "code": "000660", "market": "KOSPI",
         "note": "인디애나 HBM 패키징 2028 가동"},
        {"name": "한미반도체",   "code": "042700", "market": "KOSPI",
         "note": "HBM TC본더 글로벌 1위"},
        {"name": "솔브레인",     "code": "357780", "market": "KOSDAQ",
         "note": "반도체 화학 소재"},
        {"name": "리노공업",     "code": "058470", "market": "KOSDAQ",
         "note": "반도체 테스트 핀"},
    ],
    "자동차": [
        {"name": "현대차",       "code": "005380", "market": "KOSPI",
         "note": "조지아 메타플랜트 가동"},
        {"name": "기아",         "code": "000270", "market": "KOSPI",
         "note": "조지아 공장"},
        {"name": "현대모비스",   "code": "012330", "market": "KOSPI",
         "note": "자동차 부품 현지화"},
        {"name": "LG에너지솔루션", "code": "373220", "market": "KOSPI",
         "note": "배터리 IRA 보조금 변수"},
        {"name": "삼성SDI",       "code": "006400", "market": "KOSPI",
         "note": "전기차 배터리"},
    ],
    "조선": [
        {"name": "HD현대중공업",   "code": "329180", "market": "KOSPI",
         "note": "MASGA 핵심, 美 함정 MRO"},
        {"name": "한화오션",       "code": "042660", "market": "KOSPI",
         "note": "필리쉽야드 인수, 美 조선소"},
        {"name": "삼성중공업",     "code": "010140", "market": "KOSPI",
         "note": "LNG선·해양플랜트"},
        {"name": "HD한국조선해양", "code": "009540", "market": "KOSPI",
         "note": "조선 지주"},
    ],
    "원자력/에너지": [
        {"name": "두산에너빌리티", "code": "034020", "market": "KOSPI",
         "note": "SMR·원전 EPC"},
        {"name": "한전기술",       "code": "052690", "market": "KOSPI",
         "note": "원전 설계"},
        {"name": "한전KPS",        "code": "051600", "market": "KOSPI",
         "note": "원전 정비"},
        {"name": "효성중공업",     "code": "298040", "market": "KOSPI",
         "note": "변압기 미국 수출"},
        {"name": "HD현대일렉트릭", "code": "267260", "market": "KOSPI",
         "note": "북미 변압기 수주"},
    ],
    "방산/우주": [
        {"name": "한화에어로스페이스", "code": "012450", "market": "KOSPI",
         "note": "K9·천궁·우주발사체"},
        {"name": "현대로템",          "code": "064350", "market": "KOSPI",
         "note": "K2 전차"},
        {"name": "LIG넥스원",         "code": "079550", "market": "KOSPI",
         "note": "유도무기"},
        {"name": "한국항공우주",      "code": "047810", "market": "KOSPI",
         "note": "FA-50·KF-21"},
        {"name": "쎄트렉아이",        "code": "099320", "market": "KOSDAQ",
         "note": "위성"},
    ],
    "암호화폐": [
        {"name": "갤럭시아머니트리", "code": "094480", "market": "KOSDAQ",
         "note": "결제·블록체인"},
        {"name": "위지트",          "code": "036090", "market": "KOSDAQ",
         "note": "암호화폐 거래소 빗썸 지분"},
        {"name": "우리기술투자",    "code": "041190", "market": "KOSDAQ",
         "note": "두나무 지분"},
        {"name": "한화투자증권",    "code": "003530", "market": "KOSPI",
         "note": "두나무 지분"},
    ],
    "AI/빅테크": [
        {"name": "네이버",   "code": "035420", "market": "KOSPI",
         "note": "하이퍼클로바X·국내 AI 대표"},
        {"name": "카카오",   "code": "035720", "market": "KOSPI",
         "note": "AI·플랫폼"},
        {"name": "SK텔레콤", "code": "017670", "market": "KOSPI",
         "note": "AI 데이터센터"},
        {"name": "삼성전자", "code": "005930", "market": "KOSPI",
         "note": "AI 반도체 HBM"},
    ],
    "중국 견제": [
        {"name": "삼성SDI",         "code": "006400", "market": "KOSPI",
         "note": "탈중국 배터리 수혜"},
        {"name": "에코프로비엠",    "code": "247540", "market": "KOSDAQ",
         "note": "양극재 탈중국 공급망"},
        {"name": "LG에너지솔루션",  "code": "373220", "market": "KOSPI",
         "note": "IRA·탈중국 수혜"},
        {"name": "포스코퓨처엠",    "code": "003670", "market": "KOSPI",
         "note": "양극재"},
    ],
}


# ---------------------------------------------------------------
# 4. 추가 RSS 피드 (트럼프 영향 + 공시)
# ---------------------------------------------------------------
# 기존 config.RSS_FEEDS 에 합쳐서 사용
# - 한국경제 마켓인사이트(공시·테마), 이투데이(특징주)
# - 영문은 Google News Search 기반 RSS (rate limit 가능하므로 1~2개만)
TRUMP_RSS_FEEDS = [
    {
        "name": "한국경제 국제",
        "url": "https://rss.hankyung.com/feed/international.xml",
        "category": "글로벌",
    },
    {
        "name": "한국경제 정치",
        "url": "https://rss.hankyung.com/feed/politics.xml",
        "category": "글로벌",
    },
    {
        "name": "매일경제 국제",
        "url": "https://www.mk.co.kr/rss/30300018/",
        "category": "글로벌",
    },
    {
        "name": "이투데이 증권",
        "url": "https://www.etoday.co.kr/rss/rss_section.xml?id=22",
        "category": "증시",
    },
    # 영문 트럼프 뉴스 (Google News 검색 RSS)
    {
        "name": "Google News - Trump",
        "url": "https://news.google.com/rss/search?q=trump+korea+OR+semiconductor+OR+tariff&hl=en-US&gl=US&ceid=US:en",
        "category": "글로벌",
    },
]


# ---------------------------------------------------------------
# 5. 표시 설정
# ---------------------------------------------------------------
# 트럼프 섹션에 표시할 최대 토픽 수 (관련 뉴스 0건인 토픽은 자동 숨김)
MAX_TOPICS_DISPLAYED = 8
# 토픽당 최대 뉴스 개수
MAX_NEWS_PER_TOPIC = 5
# 토픽당 최대 관련주 표시 개수
MAX_STOCKS_PER_TOPIC = 6
# 최근 N시간 이내 뉴스만 트럼프 섹션에 포함 (기존 NEWS_HOURS_WINDOW 와 별도)
TRUMP_NEWS_HOURS_WINDOW = 48
