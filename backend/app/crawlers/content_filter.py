"""
Content Filter for Outlier Crawling

강력한 필터링으로 체험단에 적합하지 않은 콘텐츠 제외:
- TV 프로그램 / 방송사 채널
- 연예인 / 아이돌 콘텐츠
- 유튜버 편집 영상 (하이라이트, 클립)
- 뉴스 / 시사 / 스포츠

사용법:
    from app.crawlers.content_filter import ContentFilter, should_collect
    
    if should_collect(title, channel_name, hashtags):
        # 수집 진행
    else:
        # 스킵
"""
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class FilterResult:
    """필터링 결과"""
    should_collect: bool
    reject_reason: Optional[str] = None
    confidence: float = 1.0


class ContentFilter:
    """
    체험단 콘텐츠 필터
    
    필터링 대상:
    1. TV 프로그램 / 방송사
    2. 연예인 / 아이돌
    3. 유튜버 편집 영상 (하이라이트, 클립)
    4. 뉴스 / 시사 / 스포츠
    5. 재현 불가능한 콘텐츠
    """
    
    # ==================== 방송사 / TV 채널 ====================
    BROADCAST_CHANNELS = {
        # 지상파
        "sbs", "kbs", "mbc", "ebs",
        # 케이블
        "tvn", "jtbc", "mnet", "ocn", "cj enm",
        "channel a", "채널a", "tv조선", "mbn",
        # 유튜브 공식 채널
        "sbs entertainment", "kbs entertainment", "mbc entertainment",
        "tvn drama", "jtbc entertainment", "mnet k-pop",
        "sbs drama", "kbs drama", "mbc drama",
        # 예능
        "놀면뭐하니", "런닝맨", "무한도전", "삼시세끼",
        "나혼자산다", "전지적참견시점", "유퀴즈", "놀라운토요일",
        "1박2일", "신서유기", "강식당", "윤스테이",
        "출장십오야", "아는형님", "미운우리새끼", "슈가맨",
    }
    
    # ==================== TV 프로그램 키워드 ====================
    TV_PROGRAM_KEYWORDS = [
        # 예능 프로그램
        r"극한\d+", r"극한직업", "나혼산", "전참시", 
        "런닝맨", "무도", "놀뭐", "삼시세끼",
        "유퀴즈", "아형", "신서유기", "놀토",
        # 드라마
        "드라마", "본방", "재방", "하이라이트",
        # 방송 관련
        r"\d+회", r"\d+화", "예고", "미리보기",
        "본편", "풀버전", "비하인드", "메이킹",
        # 클립 형태
        "편집영상", "명장면", "레전드", "cut", "clip",
    ]
    
    # ==================== 연예인 / 아이돌 키워드 ====================
    CELEBRITY_KEYWORDS = [
        # 직접 표시
        "연예인", "아이돌", "셀럽", "스타",
        "배우", "가수", "모델", "mc",
        # 아이돌 그룹 (주요)
        "bts", "방탄소년단", "blackpink", "블랙핑크",
        "newjeans", "뉴진스", "aespa", "에스파",
        "twice", "트와이스", "itzy", "있지",
        "stray kids", "스트레이키즈", "nct", "엔시티",
        "seventeen", "세븐틴", "txt", "투바투",
        "ive", "아이브", "lesserafim", "르세라핌",
        # 솔로 아티스트 (주요)
        "아이유", "iu", "태연", "제니", "지수",
        # 예능인
        "유재석", "강호동", "이수근", "신동엽",
        "이경규", "김구라", "서장훈", "김희철",
        # 배우 (주요)
        "송강호", "마동석", "전종서", "박서준",
    ]
    
    # ==================== 편집/클립 영상 패턴 ====================
    EDIT_CLIP_PATTERNS = [
        r"#?\s*shorts?\s*편집",
        r"하이라이트",
        r"명장면",
        r"레전드\s*(장면|모음|씬)",
        r"best\s*(moment|scene)",
        r"cut\s*모음",
        r"\d+분\s*요약",
        r"총정리",
        r"몰아보기",
        r"다시보기",
    ]
    
    # ==================== 제외 해시태그 ====================
    EXCLUDE_HASHTAGS = {
        "#연예인", "#아이돌", "#셀럽", "#스타",
        "#드라마", "#예능", "#방송", "#tv",
        "#kpop", "#케이팝", "#아이돌직캠", "#fancam",
        "#본방", "#재방", "#풀버전",
        "#뉴스", "#시사", "#정치",
        "#스포츠", "#축구", "#야구", "#농구",
    }
    
    # ==================== 뉴스/시사/스포츠 ====================
    NEWS_SPORTS_KEYWORDS = [
        "뉴스", "news", "속보", "breaking",
        "시사", "정치", "대통령", "국회",
        "축구", "야구", "농구", "배구", "골프",
        "프리미어리그", "라리가", "분데스리가",
        "올림픽", "월드컵", "아시안게임",
        "손흥민", "이강인", "오타니",
    ]
    
    def __init__(self):
        # 정규식 컴파일
        self._tv_patterns = [re.compile(p, re.IGNORECASE) for p in self.TV_PROGRAM_KEYWORDS]
        self._edit_patterns = [re.compile(p, re.IGNORECASE) for p in self.EDIT_CLIP_PATTERNS]
    
    def filter(
        self,
        title: str,
        channel_name: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> FilterResult:
        """
        콘텐츠 필터링
        
        Returns:
            FilterResult: should_collect=True면 수집, False면 스킵
        """
        title_lower = title.lower() if title else ""
        channel_lower = channel_name.lower() if channel_name else ""
        desc_lower = description.lower() if description else ""
        hashtags_lower = {h.lower() for h in (hashtags or [])}
        
        # 1. 방송사 채널 체크
        for broadcast in self.BROADCAST_CHANNELS:
            if broadcast in channel_lower:
                return FilterResult(
                    should_collect=False,
                    reject_reason=f"broadcast_channel:{broadcast}",
                    confidence=0.95
                )
        
        # 2. TV 프로그램 키워드 체크
        for pattern in self._tv_patterns:
            if pattern.search(title_lower) or pattern.search(desc_lower):
                return FilterResult(
                    should_collect=False,
                    reject_reason=f"tv_program:{pattern.pattern}",
                    confidence=0.9
                )
        
        # 3. 연예인/아이돌 키워드 체크
        combined_text = f"{title_lower} {channel_lower} {desc_lower}"
        for celeb in self.CELEBRITY_KEYWORDS:
            if celeb.lower() in combined_text:
                return FilterResult(
                    should_collect=False,
                    reject_reason=f"celebrity:{celeb}",
                    confidence=0.85
                )
        
        # 4. 편집/클립 영상 패턴 체크
        for pattern in self._edit_patterns:
            if pattern.search(title_lower) or pattern.search(desc_lower):
                return FilterResult(
                    should_collect=False,
                    reject_reason=f"edit_clip:{pattern.pattern}",
                    confidence=0.85
                )
        
        # 5. 제외 해시태그 체크
        for exclude_tag in self.EXCLUDE_HASHTAGS:
            if exclude_tag.lower() in hashtags_lower:
                return FilterResult(
                    should_collect=False,
                    reject_reason=f"hashtag:{exclude_tag}",
                    confidence=0.9
                )
        
        # 6. 뉴스/시사/스포츠 체크
        for keyword in self.NEWS_SPORTS_KEYWORDS:
            if keyword.lower() in combined_text:
                return FilterResult(
                    should_collect=False,
                    reject_reason=f"news_sports:{keyword}",
                    confidence=0.8
                )
        
        # 모든 필터 통과
        return FilterResult(should_collect=True)
    
    def get_remixable_score(
        self,
        title: str,
        channel_name: Optional[str] = None,
        view_count: int = 0,
        like_count: int = 0,
    ) -> Tuple[int, List[str]]:
        """
        Remixable 점수 계산 (5-Point 체크리스트 간소화 버전)
        
        Returns:
            Tuple[score (0-10), reasons]
        """
        score = 5  # 기본 점수
        reasons = []
        
        # 높은 인게이지먼트 가산
        if view_count > 0 and like_count > 0:
            engagement = like_count / view_count
            if engagement > 0.1:  # 10%+
                score += 2
                reasons.append("high_engagement")
            elif engagement > 0.05:  # 5%+
                score += 1
                reasons.append("good_engagement")
        
        # 간단한 제목 (복잡한 스토리 아님)
        if len(title) < 50:
            score += 1
            reasons.append("simple_title")
        
        # 개인 크리에이터 추정 (방송사 아님)
        if channel_name:
            is_personal = not any(
                b in channel_name.lower() 
                for b in self.BROADCAST_CHANNELS
            )
            if is_personal:
                score += 2
                reasons.append("personal_creator")
        
        return min(score, 10), reasons


# 싱글톤 인스턴스
content_filter = ContentFilter()


def should_collect(
    title: str,
    channel_name: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> bool:
    """편의 함수: 수집 여부만 반환"""
    result = content_filter.filter(title, channel_name, hashtags, description)
    return result.should_collect


def filter_with_reason(
    title: str,
    channel_name: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> FilterResult:
    """편의 함수: 필터 결과 전체 반환"""
    return content_filter.filter(title, channel_name, hashtags, description)


@dataclass
class UGCCheckResult:
    """UGC 친화도 체크 결과"""
    is_filmable: bool
    reject_reasons: List[str]
    score: int  # 0-100


def is_creator_filmable(
    duration_sec: int = 60,
    creator_followers: int = 0,
    title: str = "",
    description: str = "",
) -> UGCCheckResult:
    """
    핸드폰 촬영 가능 여부 판단 (UGC 친화도)
    
    Research-based criteria:
    1. 영상 길이 <= 60초
    2. 팔로워 < 1M (메가 인플루언서 제외)
    3. 전문 편집 흔적 없음
    4. TV/방송 콘텐츠 아님
    
    Returns:
        UGCCheckResult with filmable status and score
    """
    reasons = []
    score = 100
    
    # 1. 영상 길이 체크 (60초 이하)
    if duration_sec > 60:
        reasons.append(f"too_long:{duration_sec}s")
        score -= 30
    
    # 2. 팔로워 수 체크 (메가 인플루언서 제외)
    if creator_followers >= 1_000_000:
        reasons.append(f"mega_influencer:{creator_followers}")
        score -= 40
    elif creator_followers >= 500_000:
        # 중형 인플루언서는 페널티 적음
        score -= 10
    
    # 3. 전문 편집 흔적 체크
    professional_edit_keywords = [
        "vfx", "cgi", "3d", "모션그래픽",
        "전문촬영", "drone", "드론", "촬영팀",
        "스튜디오", "studio", "제작사",
    ]
    combined_text = f"{title} {description}".lower()
    for keyword in professional_edit_keywords:
        if keyword in combined_text:
            reasons.append(f"professional_edit:{keyword}")
            score -= 25
            break
    
    # 4. TV/방송 콘텐츠 체크 (기존 필터 활용)
    filter_result = content_filter.filter(title, description=description)
    if not filter_result.should_collect:
        reasons.append(filter_result.reject_reason or "content_filter")
        score -= 50
    
    # 최종 판단
    is_filmable = len(reasons) == 0 and score >= 60
    
    return UGCCheckResult(
        is_filmable=is_filmable,
        reject_reasons=reasons,
        score=max(0, score)
    )


# Hook 패턴 분류 (UGC 리서치 기반)
HOOK_PATTERNS = {
    "reaction_face": "표정 리액션 (첫 0.5초)",
    "product_reveal": "제품 공개 (언박싱)",
    "food_first_bite": "첫 입 클로즈업 (먹방)",
    "before_after": "전후 비교",
    "pov_approach": "POV 진입",
    "text_hook": "텍스트 후킹",
    "question_hook": "질문형 후킹",
}

