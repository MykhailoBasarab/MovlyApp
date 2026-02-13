from openai import OpenAI
from django.conf import settings
from typing import Optional
import json
import re


class AIExerciseService:
    """Сервіс для роботи з AI для генерації та перевірки вправ"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
    
    def generate_exercise(
        self,
        lesson_topic: str,
        exercise_type: str,
        language: str = 'en',
        level: str = 'beginner'
    ) -> Optional[dict]:
        """
        Генерує вправу за допомогою AI
        
        Args:
            lesson_topic: Тема уроку
            exercise_type: Тип вправи
            language: Мова вивчення
            level: Рівень складності
        
        Returns:
            dict з полями: question, correct_answer, options (якщо потрібно)
        """
        if not self.api_key:
            return None
        
        if not self.client:
            return None
        
        try:
            prompt = self._build_generation_prompt(
                lesson_topic,
                exercise_type,
                language,
                level
            )
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ти допомагаєш створювати вправи для вивчення мов."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            return self._parse_exercise_response(result, exercise_type)
            
        except Exception as e:
            print(f"Помилка генерації вправи: {e}")
            return None
    
    def get_feedback(
        self,
        question: str,
        correct_answer: str,
        user_answer: str,
        exercise_type: str
    ) -> Optional[str]:
        """
        Отримує відгук AI на відповідь користувача
        
        Args:
            question: Питання вправи
            correct_answer: Правильна відповідь
            user_answer: Відповідь користувача
            exercise_type: Тип вправи
        
        Returns:
            Текст відгуку
        """
        if not self.api_key:
            return None
        
        if not self.client:
            return None
        
        try:
            prompt = f"""
            Надай конструктивний відгук на відповідь студента.
            
            Питання: {question}
            Правильна відповідь: {correct_answer}
            Відповідь студента: {user_answer}
            Тип вправи: {exercise_type}
            
            Надай короткий, корисний відгук українською мовою. Якщо відповідь неправильна, поясни помилку та дай підказку.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ти вчитель мов, який надає корисні відгуки студентам."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Помилка отримання відгуку: {e}")
            return None
    
    def check_answer_with_ai(
        self,
        question: str,
        correct_answer: str,
        user_answer: str
    ) -> tuple[bool, Optional[str]]:
        """
        Перевіряє відповідь за допомогою AI (для складних випадків)
        
        Returns:
            tuple: (is_correct, feedback)
        """
        if not self.api_key:
            return False, None
        
        if not self.client:
            return False, None
        
        try:
            prompt = f"""
            Перевір відповідь студента на питання.
            
            Питання: {question}
            Правильна відповідь: {correct_answer}
            Відповідь студента: {user_answer}
            
            Відповісти тільки: CORRECT або INCORRECT, потім через новий рядок короткий відгук українською.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ти перевіряєш відповіді студентів."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            is_correct = result.startswith('CORRECT')
            feedback = '\n'.join(result.split('\n')[1:]) if '\n' in result else None
            
            return is_correct, feedback
            
        except Exception as e:
            print(f"Помилка перевірки відповіді: {e}")
            return False, None
    
    def _build_generation_prompt(
        self,
        topic: str,
        exercise_type: str,
        language: str,
        level: str
    ) -> str:
        """Побудова промпту для генерації вправи"""
        type_descriptions = {
            'multiple_choice': 'Вправа з вибором правильної відповіді з кількох варіантів',
            'fill_blank': 'Вправа на заповнення пропуску',
            'translation': 'Вправа на переклад',
            'listening': 'Вправа на аудіювання',
            'speaking': 'Вправа на говоріння',
        }
        
        return f"""
        Створи вправу для вивчення {language} мови.
        
        Тема: {topic}
        Тип вправи: {type_descriptions.get(exercise_type, exercise_type)}
        Рівень: {level}
        
        Формат відповіді (JSON):
        {{
            "question": "текст питання",
            "correct_answer": "правильна відповідь",
            "options": ["варіант1", "варіант2", "варіант3", "варіант4"] (тільки для multiple_choice)
        }}
        
        Створи вправу відповідно до рівня складності.
        """
    
    def _parse_exercise_response(self, response: str, exercise_type: str) -> dict:
        """Парсинг відповіді AI"""
        # Спрощений парсинг (в реальному проекті краще використовувати JSON)
        import json
        
        try:
            # Спробуємо знайти JSON в відповіді
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Якщо не вдалося розпарсити JSON, повертаємо базову структуру
        lines = response.split('\n')
        question = lines[0] if lines else "Вправа"
        correct_answer = lines[1] if len(lines) > 1 else "Відповідь"
        
        result = {
            'question': question,
            'correct_answer': correct_answer,
        }
        
        if exercise_type == 'multiple_choice' and len(lines) > 2:
            result['options'] = [line.strip('- ').strip() for line in lines[2:6] if line.strip()]
        
        return result


class AITextToSpeechService:
    """Сервіс для генерації аудіо через AI (Text-to-Speech)"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = None
        if self.api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
    
    def generate_speech(self, text: str, language: str = 'en') -> Optional[str]:
        """
        Генерує аудіо з тексту через OpenAI TTS API
        
        Args:
            text: Текст для озвучування
            language: Мова тексту
        
        Returns:
            URL або шлях до згенерованого аудіо файлу
        """
        if not self.api_key:
            return None
        
        if not self.client:
            return None
        
        try:
            # Використовуємо OpenAI TTS API
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # Можна вибрати: alloy, echo, fable, onyx, nova, shimmer
                input=text
            )
            
            # Зберігаємо аудіо файл
            # В реальному проекті тут буде збереження файлу та повернення URL
            # Для прикладу повертаємо заглушку
            # response.stream_to_file(f"media/audio/{hash(text)}.mp3")
            return f"/media/audio/{hash(text)}.mp3"
            
        except Exception as e:
            print(f"Помилка генерації аудіо: {e}")
            # Fallback: використовуємо інший сервіс або повертаємо None
            return None
    
    def generate_listening_audio(
        self,
        text: str,
        language: str = 'en',
        speed: float = 1.0
    ) -> Optional[str]:
        """
        Генерує аудіо для аудіювання з можливістю налаштування швидкості
        
        Args:
            text: Текст для озвучування
            language: Мова
            speed: Швидкість відтворення (0.5 - 2.0)
        
        Returns:
            URL до аудіо файлу
        """
        return self.generate_speech(text, language)

