"""
Claude Korean Planner - Scenario Planning Service
Uses Anthropic's Claude 3.5 Sonnet to generate culturally nuanced Korean meme scenarios.
"""
import json
from enum import Enum
from typing import List, Optional
from anthropic import AsyncAnthropic
from app.config import settings

# Define input structure (aligned with Gemini Output)
class MemeDNA(str, Enum):
    DANCE = "dance"
    LIPSYNC = "lipsync"
    SKIT = "skit"
    CHALLENGE = "challenge"

class ClaudeKoreanPlanner:
    def __init__(self):
        if settings.CLAUDE_API_KEY:
            self.client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
            self.model = "claude-3-5-sonnet-20240620"
        else:
            print("Warning: CLAUDE_API_KEY not set")
            self.client = None

    async def generate_scenario(self, gemini_result: dict, context: str = "general") -> dict:
        """
        Generate a Korean meme scenario based on Gemini analysis.
        """
        if not self.client:
            # Mock fallback
            return self._get_mock_scenario()

        # Construct Prompt
        # Construct Prompt
        # Support for V3 Reconstructible Schema
        global_context = gemini_result.get("global_context")
        if isinstance(global_context, dict):
            ctx = global_context
            title = ctx.get("title", "Untitled")
            mood = ctx.get("mood", "Viral")
            key_action = ctx.get("key_action_description", "")
            humor_point = ctx.get("viral_hook_summary", "")
        else:
            # Legacy Schema
            meme_dna = gemini_result.get("meme_dna")
            if not isinstance(meme_dna, dict):
                meme_dna = {}
            metadata = gemini_result.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            title = metadata.get("title")
            mood = metadata.get("mood")
            key_action = meme_dna.get("key_action")
            humor_point = meme_dna.get("humor_point")
        
        prompt = f"""
        당신은 한국의 틱톡/릴스 트렌드를 선도하는 '바이럴 콘텐츠 디렉터'입니다.
        주어진 비디오 분석 데이터(Gemini Analysis)를 바탕으로, 한국 시청자들에게 먹히는 '숏폼 챌린지 시나리오'를 기획해주세요.

        [입력 데이터]
        - Title: {title}
        - Mood: {mood}
        - Key Action: {key_action}
        - Humor Point: {humor_point}
        - Context: {context}

        [요청 사항]
        1. 시나리오 제목: 밈의 특징을 살린 한국어 제목 (예: "OOO 챌린지")
        2. Hook (초반 3초): 시선을 사로잡는 오프닝 연출
        3. Action (본문): 따라하기 쉬우면서도 재미있는 동작 설명
        4. Caption (업로드용): 필수 해시태그(#)와 함께 재치 있는 멘트

        JSON 형식으로 출력해주세요:
        {{
            "title_kr": "string",
            "hook_description": "string",
            "action_steps": ["string", "string"],
            "caption": "string",
            "hashtags": ["string"]
        }}
        """

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system="You are a creative director specialized in Korean viral culture. Output JSON only.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            return json.loads(content)
            
        except Exception as e:
            print(f"❌ Claude generation failed: {e}")
            return self._get_mock_scenario()

    def _get_mock_scenario(self) -> dict:
        """Mock scenario for development"""
        return {
            "title_kr": "스쿼트 댄스 챌린지",
            "hook_description": "음악이 시작되자마자 정색하고 스쿼트 자세를 취한다.",
            "action_steps": [
                "비트 드랍 전까지는 무표정으로 위아래 바운스를 탄다.",
                "드랍(Drop)이 터지는 순간, 친구와 서로 마주보며 막춤을 춘다.",
                "마지막엔 다시 정색하며 카메라를 응시한다."
            ],
            "caption": "이거 하다가 허벅지 터질 뻔... ㅋㅋㅋ 친구 @태그 해서 도전!",
            "hashtags": ["#스쿼트댄스", "#운동하는남자", "#헬창밈", "#Komission"]
        }

claude_planner = ClaudeKoreanPlanner()
