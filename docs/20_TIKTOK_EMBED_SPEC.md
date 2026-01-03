# TikTok Embed 역공학 문서 (Virlo 완벽 분석)

**작성일**: 2025-12-30
**분석 대상**: https://app.virlo.ai/outlier
**목적**: TikTok 영상 임베드를 100% 재현 가능하도록 완전한 기술 사양 문서화

---

## 1. 핵심 발견 사항

### 1.1 임베드 URL 형식

TikTok은 두 가지 공식 임베드 방식을 제공하지만, **v1 Player API**가 더 안정적임:

| 방식 | URL 형식 | 안정성 |
|------|----------|--------|
| ❌ Embed v2 | `https://www.tiktok.com/embed/v2/{id}` | 불안정, CSP 오류 발생 |
| ✅ Player v1 | `https://www.tiktok.com/player/v1/{id}` | 안정적, Virlo 사용 중 |

### 1.2 비디오 ID 요구사항

```
⚠️ 중요: 반드시 실제 존재하는 TikTok 비디오 ID를 사용해야 함!
가짜/placeholder ID → "Video currently unavailable" 오류
```

**비디오 ID 형식:**
- 길이: 18-20자리 숫자
- 예시: `7589283597429869857`
- 출처: TikTok URL의 `/video/{id}` 부분에서 추출

---

## 2. 완전한 iframe 구현

### 2.1 Virlo가 사용하는 정확한 코드

```html
<iframe
  src="https://www.tiktok.com/player/v1/{VIDEO_ID}?autoplay=1&loop=1&mute=1&controls=1&progress_bar=1&play_button=1&volume_control=1&fullscreen_button=1"
  class="w-full h-full"
  allowfullscreen
  allow="autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; microphone; camera"
  frameborder="0"
></iframe>
```

### 2.2 Query Parameters 상세 설명

| Parameter | 값 | 설명 | 필수 여부 |
|-----------|----|----|---------|
| `autoplay` | `1` | 자동 재생 활성화 | 권장 |
| `loop` | `1` | 반복 재생 | 권장 |
| **`mute`** | **`1`** | **음소거 (autoplay 작동 필수!)** | **필수** |
| `controls` | `1` | 플레이어 컨트롤 표시 | 권장 |
| `progress_bar` | `1` | 진행 바 표시 | 선택 |
| `play_button` | `1` | 재생 버튼 표시 | 선택 |
| `volume_control` | `1` | 볼륨 조절 표시 | 선택 |
| `fullscreen_button` | `1` | 전체 화면 버튼 표시 | 선택 |

> **⚠️ 중요**: `mute=1`이 없으면 브라우저의 autoplay 정책으로 인해 영상이 자동 재생되지 않음!

### 2.3 iframe allow 속성

```
allow="autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; microphone; camera"
```

| Permission | 용도 |
|------------|------|
| `autoplay` | 자동 재생 허용 |
| `clipboard-write` | 공유 시 클립보드 복사 |
| `encrypted-media` | DRM 콘텐츠 재생 |
| `gyroscope` | 모바일 회전 감지 |
| `picture-in-picture` | PIP 모드 |
| `web-share` | 웹 공유 API |
| `microphone`, `camera` | 듀엣/리액션 기능 (향후) |

---

## 2.4 음소거 해제(Unmute) 버튼 오버레이

TikTok 임베드는 브라우저 autoplay 정책으로 인해 **반드시 음소거 상태로 시작**해야 합니다.
Virlo는 이를 해결하기 위해 별도의 **Unmute 버튼 오버레이**를 구현합니다.

### 버튼 위치 및 스타일

```tsx
<button
    onClick={() => setIsMuted(!isMuted)}
    className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-black/50 backdrop-blur-sm border border-white/20 hover:bg-black/70 transition-colors z-10"
>
    {/* SVG 아이콘 */}
</button>
```

| 속성 | 값 | 설명 |
|------|----|----|
| **위치** | `left-4 top-1/2 -translate-y-1/2` | 비디오 좌측 중앙 |
| **크기** | `p-3` (~50x50px) | 24px 아이콘 + 12px 패딩 |
| **배경** | `bg-black/50` | 50% 투명 검은색 |
| **블러** | `backdrop-blur-sm` | 약간 흐림 효과 |
| **테두리** | `border border-white/20` | 20% 흰색 1px 라인 |
| **호버** | `hover:bg-black/70` | 호버 시 더 어두움 |

### SVG 아이콘

**음소거 상태 (Muted)** - 스피커 + X:
```html
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
    <line x1="23" y1="9" x2="17" y2="15" />
    <line x1="17" y1="9" x2="23" y2="15" />
</svg>
```

**음소거 해제 (Unmuted)** - 스피커 + 웨이브:
```html
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
    <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
</svg>
```

### 동작 방식 (postMessage API)

Virlo는 iframe을 리로드하지 않고 **postMessage**로 TikTok 플레이어를 제어합니다:

```tsx
const iframeRef = useRef<HTMLIFrameElement>(null);
const [isMuted, setIsMuted] = useState(true);

const handleToggleMute = () => {
    const iframe = iframeRef.current;
    if (!iframe?.contentWindow) return;

    // Virlo's exact postMessage format for TikTok
    // NOTE: 'unMute' has capital M - case-sensitive!
    iframe.contentWindow.postMessage({
        type: isMuted ? 'unMute' : 'mute',
        'x-tiktok-player': true,
        value: undefined
    }, '*');

    setIsMuted(!isMuted);
};
```

> **⚠️ 중요**: iframe의 src를 변경하여 리로드하면 영상이 처음부터 다시 시작됩니다.
> postMessage를 사용하면 영상 재생이 끊기지 않고 바로 음소거가 해제됩니다.

### 3.1 TypeScript/JavaScript

```typescript
/**
 * TikTok URL에서 비디오 ID 추출
 * 
 * 지원 URL 형식:
 * - https://www.tiktok.com/@username/video/7589283597429869857
 * - https://www.tiktok.com/v/7589283597429869857
 * - https://vm.tiktok.com/XXXXXX (단축 URL: 현재 프론트엔드에서는 리다이렉트 해제 미지원)
 */
function extractTikTokVideoId(url: string): string | null {
    if (!url) return null;

    const patterns = [
        /video\/(\d+)/,           // /@user/video/123456789
        /\/v\/(\d+)/,             // /v/123456789
        /tiktok\.com\/.*?(\d{15,})/ // 15자리 이상 숫자
    ];

    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }
    return null;
}

// 사용 예시
const videoId = extractTikTokVideoId("https://www.tiktok.com/@omoekitinews/video/7589283597429869857");
// → "7589283597429869857"
```

### 3.2 Python

```python
import re

def extract_tiktok_video_id(url: str) -> str | None:
    """TikTok URL에서 비디오 ID 추출"""
    if not url:
        return None
    
    patterns = [
        r'video/(\d+)',
        r'/v/(\d+)',
        r'tiktok\.com/.*?(\d{15,})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
```

---

## 4. React 컴포넌트 완전 구현

```tsx
interface TikTokEmbedProps {
    videoUrl: string;
    autoplay?: boolean;
    muted?: boolean;
    loop?: boolean;
    className?: string;
}

export function TikTokEmbed({ 
    videoUrl, 
    autoplay = true, 
    muted = true, 
    loop = true,
    className = "w-full h-full"
}: TikTokEmbedProps) {
    const videoId = extractTikTokVideoId(videoUrl);
    
    if (!videoId) {
        return (
            <div className="flex items-center justify-center h-full bg-black/50 text-white">
                <span>⚠️ 유효하지 않은 TikTok URL</span>
            </div>
        );
    }
    
    // Virlo와 동일한 파라미터
    const params = new URLSearchParams({
        autoplay: autoplay ? '1' : '0',
        loop: loop ? '1' : '0',
        mute: muted ? '1' : '0',  // ⚠️ 필수!
        controls: '1',
        progress_bar: '1',
        play_button: '1',
        volume_control: '1',
        fullscreen_button: '1'
    });
    
    const embedUrl = `https://www.tiktok.com/player/v1/${videoId}?${params}`;
    
    return (
        <iframe
            src={embedUrl}
            className={className}
            allowFullScreen
            allow="autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; microphone; camera"
            frameBorder="0"
        />
    );
}
```

---

## 5. 썸네일 프록시 (Virlo 방식)

Virlo는 TikTok CDN 직접 접근 시 발생하는 CORS/hotlink 문제를 우회하기 위해 `weserv.nl` 프록시를 사용:

```typescript
function getTikTokThumbnailProxy(originalUrl: string): string {
    // weserv.nl 이미지 프록시를 통해 CORS 우회
    return `https://images.weserv.nl/?url=${encodeURIComponent(originalUrl)}`;
}

// 또는 Next.js Image 최적화 사용
// <Image src={thumbnailUrl} loader={weservLoader} />
```

---

## 6. 흔한 오류 및 해결책

| 오류 | 원인 | 해결책 |
|------|------|--------|
| "Video currently unavailable" | 가짜/존재하지 않는 비디오 ID | 실제 TikTok 비디오 ID 사용 |
| 자동 재생 안 됨 | `mute=1` 누락 | `mute=1` 파라미터 추가 |
| iframe 로드 실패 | 잘못된 allow 속성 | 전체 allow 문자열 복사 |
| 썸네일 404 | TikTok CDN 만료 | 프록시 사용 또는 자체 호스팅 |
| CSP 오류 | embed/v2 사용 | player/v1 사용 |

---

## 7. 테스트용 실제 비디오 ID (2025-12-30 기준)

Virlo에서 추출한 검증된 비디오 ID:

| Video ID | Creator | Category |
|----------|---------|----------|
| `7589283597429869857` | @omoekitinews | News |
| `7589280628135316758` | @meow08183 | Gaming |
| `7589269856713706774` | @skiptotheweirdbit | News |
| `7589246764234935573` | @clashelite_ | Gaming |
| `7589234035134713095` | @fastbreakfilms24 | Sports |
| `7589226569500019982` | @bransonhtreytrelo | News |
| `7589226468517874966` | @foodiegirlsarah | Cooking |
| `7589216676349054230` | @havexuniverse | Gaming |
| `7589206861111364871` | @this.is.oscar_ | Comedy |
| `7589195251890326806` | @kamila_clips | Gaming |

---

## 8. 체크리스트

구현 전 확인:

- [ ] 비디오 URL에 `/video/{id}` 형식이 포함되어 있는가?
- [ ] 비디오 ID가 18-20자리 숫자인가?
- [ ] `mute=1` 파라미터가 포함되어 있는가?
- [ ] iframe allow 속성이 완전한가?
- [ ] 프로덕션에서 실제 비디오 ID를 사용하는가?

---

## 참고자료

- Virlo 분석 일시: 2025-12-30
- TikTok Player API: 비공식, 역공학 기반
- 관련 파일: `/frontend/src/app/ops/outliers/page.tsx`
