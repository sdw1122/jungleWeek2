import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.ai_service import DEFAULT_MODEL, analyze_chat, build_personality


class AiServiceTestCase(unittest.TestCase):
    def test_missing_api_key_uses_local_response(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            result = analyze_chat("예쁘게 자라줘")

        self.assertEqual(result["sentiment"], "POSITIVE")
        self.assertEqual(result["positive_delta"], 1)

    @patch("app.services.ai_service.OpenAI")
    def test_openai_uses_gpt_luna_responses_api(self, openai_class):
        client = MagicMock()
        client.responses.create.return_value = SimpleNamespace(
            output_text=json.dumps(
                {
                    "sentiment": "POSITIVE",
                    "emotion": "기쁨",
                    "response": "햇살처럼 따뜻한 말 고마워요!",
                    "positive_delta": 4,
                    "negative_delta": 0,
                }
            )
        )
        openai_class.return_value = client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": DEFAULT_MODEL},
        ):
            result = analyze_chat(
                "오늘도 잘 자라줘",
                [{"role": "USER", "content": "안녕"}],
                5,
                0,
                45,
                "SUNLIGHT",
                "찬란한 새벽의 몬스테라",
            )

        self.assertEqual(result["sentiment"], "POSITIVE")
        self.assertEqual(result["positive_delta"], 4)
        request = client.responses.create.call_args.kwargs
        self.assertIn("희망을 품은 봉오리", request["instructions"])
        self.assertIn(
            "희망을 품은 봉오리인 찬란한 새벽의 몬스테라",
            request["instructions"],
        )
        self.assertIn("현재 성장도는 45", request["instructions"])
        self.assertIn("가장 최근 돌봄 행동은 '햇빛 쬐어주기'", request["instructions"])
        self.assertEqual(request["model"], "gpt-5.6-luna")
        self.assertEqual(request["reasoning"], {"effort": "low"})
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        properties = request["text"]["format"]["schema"]["properties"]
        self.assertEqual(properties["positive_delta"]["maximum"], 5)
        self.assertEqual(properties["negative_delta"]["maximum"], 5)
        self.assertFalse(request["store"])
        client.close.assert_called_once()

    @patch("app.services.ai_service.OpenAI")
    def test_openai_failure_falls_back_locally(self, openai_class):
        client = MagicMock()
        client.responses.create.side_effect = RuntimeError("temporary failure")
        openai_class.return_value = client

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            result = analyze_chat("싫어")

        self.assertEqual(result["sentiment"], "NEGATIVE")
        self.assertEqual(result["negative_delta"], 1)
        client.close.assert_called_once()

    def test_local_response_can_score_stronger_impact(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            positive = analyze_chat("진짜 너무 사랑하고 고마워")
            neutral = analyze_chat("오늘 날씨를 보고 있어")

        self.assertEqual(positive["positive_delta"], 4)
        self.assertEqual(neutral["sentiment"], "NEUTRAL")
        self.assertEqual(neutral["positive_delta"], 0)
        self.assertEqual(neutral["negative_delta"], 0)

    def test_personality_uses_growth_stage_and_energy_balance(self):
        negative_bud = build_personality(
            45,
            10,
            20,
            "IGNORE",
            "뒤틀린 황천의 몬스테라",
        )
        positive_flower = build_personality(
            70,
            20,
            20,
            plant_name="찬란한 새벽의 몬스테라",
        )

        self.assertIn("뒤틀린 황천의 봉오리", negative_bud)
        self.assertIn(
            "뒤틀린 황천의 봉오리인 뒤틀린 황천의 몬스테라",
            negative_bud,
        )
        self.assertIn("까칠하고 적대적인 반려식물", negative_bud)
        self.assertIn("가장 최근 돌봄 행동은 '방치하기'", negative_bud)
        self.assertIn("축복의 꽃", positive_flower)
        self.assertIn("축복의 꽃인 찬란한 새벽의 몬스테라", positive_flower)
        self.assertIn("밝고 긍정적이며 다정하다", positive_flower)
        self.assertIn("아직 기록된 돌봄 행동은 없다", positive_flower)


if __name__ == "__main__":
    unittest.main()
