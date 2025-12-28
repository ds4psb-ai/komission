from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'

def check_quota():
    try:
        creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        service = build('drive', 'v3', credentials=creds)

        about = service.about().get(fields="user,storageQuota").execute()

        print("--- 서비스 계정 정보 ---")
        print(f"이름: {about['user']['displayName']}")
        print(f"이메일: {about['user']['emailAddress']}")
        print(f"Me: {about['user']['me']}")
        print("-" * 20)
        
        limit = int(about['storageQuota'].get('limit', 0))
        usage = int(about['storageQuota'].get('usage', 0))
        usage_drive = int(about['storageQuota'].get('usageInDrive', 0))
        usage_trash = int(about['storageQuota'].get('usageInDriveTrash', 0))
        
        print("--- 저장 용량 ---")
        print(f"전체 한도: {limit / (1024**3):.2f} GB" if limit else "무제한 (또는 알 수 없음, 0)")
        print(f"총 사용량: {usage / (1024**3):.2f} GB")
        print(f"드라이브 사용: {usage_drive / (1024**3):.2f} GB")
        print(f"휴지통 사용: {usage_trash / (1024**3):.2f} GB")

    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    check_quota()
