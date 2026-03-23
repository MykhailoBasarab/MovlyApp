from openai import OpenAI
from django.conf import settings
from typing import Optional
import json
import re
import httpx


class AIExerciseService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key, http_client=httpx.Client(trust_env=False)
                )
            except Exception as e:
                print(f"Помилка ініціалізації OpenAI: {e}")

    def generate_exercise(
        self,
        lesson_topic: str,
        exercise_type: str,
        language: str = "en",
        level: str = "beginner",
    ) -> Optional[dict]:
        if not self.api_key:
            return None

        if not self.client:
            return None

        try:
            prompt = self._build_generation_prompt(
                lesson_topic, exercise_type, language, level
            )

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Ти допомагаєш створювати вправи для вивчення мов.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            result = response.choices[0].message.content
            return self._parse_exercise_response(result, exercise_type)

        except Exception as e:
            print(f"Помилка генерації вправи: {e}")
            return None

    def check_answer_and_get_feedback(
        self,
        question: str,
        correct_answer: str,
        user_answer: str,
        exercise_type: str = "short_answer",
    ) -> dict:
        """
        Об'єднана перевірка: отримує і статус правильності, і фідбек одним запитом.
        Це гарантує консистентність (щоб не було 'Правильно', але з негативним фідбеком).
        """
        if not self.api_key or not self.client:
            return {"is_correct": False, "feedback": "AI-сервіс тимчасово недоступний."}

        try:
            prompt = f"""
            Task: Act as a professional language teacher. Evaluate the user's answer.
            
            Question: {question}
            Reference Answer/Criteria: {correct_answer}
            User's Answer: {user_answer}
            Exercise Type: {exercise_type}
            
            Requirements:
            1. Determine if the answer is correct (True/False). Be strict but fair. "I don't know" or empty/irrelevant answers are ALWAYS False.
            2. Provide a short, encouraging feedback in Ukrainian. If wrong, explain why and give a hint.
            3. Return only valid JSON.
            
            Format:
            {{
                "is_correct": boolean,
                "feedback": "string (Ukrainian)"
            }}
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a language teacher. Respond ONLY with JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            return {
                "is_correct": bool(result.get("is_correct", False)),
                "feedback": result.get("feedback", ""),
            }

        except Exception as e:
            print(f"Помилка комбінованої перевірки: {e}")
            return {
                "is_correct": False,
                "feedback": "Сталася помилка при перевірці AI.",
            }

    def generate_lesson_content(
        self, topic: str, language: str, level: str
    ) -> Optional[str]:
        if not self.api_key or not self.client:
            return None

        try:
            prompt = f"""
            Створи захоплюючий та глибокий навчальний матеріал для уроку іноземної мови.
            
            Мова вивчення: {language}
            Рівень: {level}
            Тема: {topic}
            
            Вимоги до контенту:
            1. Детальне пояснення теми з акцентом на нюанси, а не лише на базові правила.
            2. "Живі" приклади речень: використовуй сучасний сленг (якщо доречно), ідіоми або ділові ситуації з перекладом на українську.
            3. Словничок (15-20 слів) з транскрипцією, перекладом та коротким прикладом вживання для кожного слова.
            4. Розділ "Чи знаєте ви?": цікаві факти про мову або культуру країни, де цією мовою розмовляють.
            5. Поради від поліглотів щодо запам'ятовування саме цієї теми.
            6. Структуруй все за допомогою Markdown. Використовуй емодзі для розділів.
            
            Відповідь надай українською мовою, але приклади та словник мають бути мовою вивчення ({language}) з перекладом.
            Зроби матеріал об'ємним, корисним та таким, що надихає.
            """

            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "Ти професійний методист і викладач іноземних мов.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Помилка генерації контенту уроку: {e}")
            return None

    def _build_generation_prompt(
        self, topic: str, exercise_type: str, language: str, level: str
    ) -> str:
        type_descriptions = {
            "multiple_choice": "Вправа з вибором правильної відповіді з кількох варіантів",
            "fill_blank": "Вправа на заповнення пропуску",
            "translation": "Вправа на переклад",
            "speaking": "Вправа на говоріння",
        }

        return f"""
        Створи цікаву та контекстну вправу для вивчення {language} мови.
        
        Тема: {topic}
        Тип вправи: {type_descriptions.get(exercise_type, exercise_type)}
        Рівень: {level}
        
        ВАЖЛИВО: 
        - Уникай занадто простих питань типу "Як перекласти hello".
        - Використовуй життєві ситуації, діалоги або короткі описи.
        - Якщо це multiple_choice, варіанти мають бути схожими, щоб змусити задуматися.
        - НЕ ПИШИ варіанти відповіді (A, B, C, D) прямо в тексті питання ("question")! Вони мають бути ТІЛЬКИ в полі "options".
        - Питання має бути пов'язане з темою "{topic}".
        
        Формат відповіді (JSON):
        {{
            "question": "текст питання (з контекстом, БЕЗ переліку варіантів в кінці)",
            "correct_answer": "правильна відповідь",
            "options": ["варіант1", "варіант2", "варіант3", "варіант4"] (тільки для multiple_choice, НЕ ПИШИ A, B, C тут)
        }}
        """

    def _parse_exercise_response(self, response: str, exercise_type: str) -> dict:
        import json

        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        lines = response.split("\n")
        question = lines[0] if lines else "Вправа"
        correct_answer = lines[1] if len(lines) > 1 else "Відповідь"

        result = {
            "question": question,
            "correct_answer": correct_answer,
        }

        if exercise_type == "multiple_choice" and len(lines) > 2:
            result["options"] = [
                line.strip("- ").strip() for line in lines[2:6] if line.strip()
            ]

        return result
