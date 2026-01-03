# Komission Mobile App

4K 영상 촬영 + AI 코칭을 위한 모바일 앱

## 기술 스택

- **Expo SDK 52**
- **react-native-vision-camera** - 4K/H.265 촬영
- **expo-router** - 파일 기반 라우팅

## 개발 시작

```bash
# 의존성 설치
npm install

# 개발 서버 시작
npx expo start

# iOS 시뮬레이터
npx expo run:ios

# 실제 기기 테스트
npx expo start --dev-client
```

## 핵심 기능

- **4K 촬영**: 3840x2160 @ 30fps, H.265, 30Mbps
- **AI 코칭**: WebSocket 기반 실시간 피드백
- **웹앱 연결**: 딥링크로 업로드/분석

## 폴더 구조

```
mobile/
├── app/                 # expo-router 페이지
│   ├── _layout.tsx     # 루트 레이아웃
│   ├── index.tsx       # 홈 화면
│   └── camera.tsx      # 카메라 화면
├── src/
│   ├── components/     # UI 컴포넌트
│   └── hooks/          # 커스텀 훅
└── assets/             # 이미지/아이콘
```

## 백엔드 연결

WebSocket: `ws://HOST/api/v1/ws/coaching/{session_id}`

웹앱과 동일한 백엔드 API 사용
