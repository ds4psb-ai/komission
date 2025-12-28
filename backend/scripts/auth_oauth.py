"""
auth_oauth.py - OAuth 2.0 토큰 발급 스크립트

Google Drive/Sheets API에 사용자 계정으로 인증하기 위한 토큰을 발급합니다.

Prerequisites:
1. GCP Console에서 OAuth 2.0 Client ID 생성 (Desktop app)
2. JSON 다운로드 → backend/oauth_client.json으로 저장

Usage:
  cd backend
  python scripts/auth_oauth.py

결과: backend/token.json 파일 생성
"""
import os
import sys
import json
from pathlib import Path

# Path setup
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

# File paths
CLIENT_SECRETS_FILE = BASE_DIR / "oauth_client.json"
TOKEN_FILE = BASE_DIR / "token.json"


def get_credentials():
    """OAuth 인증을 수행하고 credentials를 반환합니다."""
    creds = None
    
    # 기존 토큰 로드 시도
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            print(f"✅ 기존 토큰 로드: {TOKEN_FILE}")
        except Exception as e:
            print(f"⚠️ 기존 토큰 로드 실패: {e}")
    
    # 토큰이 없거나 만료된 경우
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 토큰 갱신 중...")
            try:
                creds.refresh(Request())
                print("✅ 토큰 갱신 완료")
            except Exception as e:
                print(f"⚠️ 토큰 갱신 실패: {e}")
                creds = None
        
        if not creds:
            # Client secrets 파일 확인
            if not CLIENT_SECRETS_FILE.exists():
                print(f"❌ OAuth 클라이언트 파일을 찾을 수 없습니다: {CLIENT_SECRETS_FILE}")
                print()
                print("다음 단계를 따라 파일을 생성하세요:")
                print("1. https://console.cloud.google.com 접속")
                print("2. 프로젝트 선택 (komission-autom-v2)")
                print("3. APIs & Services > Credentials")
                print("4. + CREATE CREDENTIALS > OAuth client ID")
                print("5. Desktop app 선택")
                print("6. JSON 다운로드 → backend/oauth_client.json")
                return None
            
            print("🌐 브라우저에서 Google 계정 인증을 진행합니다...")
            print()
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), 
                SCOPES
            )
            creds = flow.run_local_server(
                port=8888, 
                success_message="인증 완료! 이 창을 닫아도 됩니다."
            )
            print("✅ 인증 완료!")
        
        # 토큰 저장
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        print(f"💾 토큰 저장: {TOKEN_FILE}")
    
    return creds


def main():
    print("=" * 50)
    print("🔐 Komission OAuth 2.0 인증")
    print("=" * 50)
    print()
    
    creds = get_credentials()
    
    if creds:
        print()
        print("=" * 50)
        print("✅ 인증 성공!")
        print(f"   토큰 파일: {TOKEN_FILE}")
        print()
        print("이제 SheetManager가 사용자 계정으로 Google Drive에 접근합니다.")
        print("=" * 50)
        return 0
    else:
        print()
        print("=" * 50)
        print("❌ 인증 실패")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    sys.exit(main())
