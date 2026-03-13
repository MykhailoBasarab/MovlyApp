from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Отримати елемент зі словника за ключем"""
    if dictionary is None:
        return None
    return dictionary.get(key)
@register.filter
def premium_label(value, lang='uk'):
    """Перетворює назви вправ на мову курсу"""
    translations = {
        'en': {
            'Вибір відповіді': 'Multiple Choice', 'Заповнити пропуск': 'Fill the Blank',
            'Переклад': 'Translation', 'Аудіювання': 'Listening', 'Говоріння': 'Speaking',
            'Згенерована': 'AI Quest', 'multiple_choice': 'Multiple Choice',
            'fill_blank': 'Fill the Blank', 'translation': 'Translation',
            'listening': 'Listening', 'speaking': 'Speaking', 'ai_generated': 'AI Quest',
            'essay': 'Essay', 'true_false': 'True/False', 'matching': 'Matching', 'short_answer': 'Short Answer'
        },
        'de': {
            'Вибір відповіді': 'Mehrfachauswahl', 'Заповнити пропуск': 'Lückentext',
            'Переклад': 'Übersetzung', 'Аудіювання': 'Hörverstehen', 'Говоріння': 'Sprechen',
            'Згенерована': 'AI-Übung', 'multiple_choice': 'Mehrfachauswahl',
            'fill_blank': 'Lückentext', 'translation': 'Übersetzung',
            'listening': 'Hörverstehen', 'speaking': 'Sprechen', 'ai_generated': 'AI-Übung',
            'essay': 'Aufsatz', 'true_false': 'Richtig/Falsch', 'matching': 'Zuordnung', 'short_answer': 'Kurzantwort'
        },
        'fr': {
            'Вибір відповіді': 'Choix multiple', 'Заповнити пропуск': 'Compléter',
            'Переклад': 'Traduction', 'Аудіювання': 'Écoute', 'Говоріння': 'Parler',
            'Згенерована': 'Exercice AI', 'multiple_choice': 'Choix multiple',
            'fill_blank': 'Compléter', 'translation': 'Traduction',
            'listening': 'Écoute', 'speaking': 'Parler', 'ai_generated': 'Exercice AI',
            'essay': 'Dissertation', 'true_false': 'Vrai/Faux', 'matching': 'Correspondance', 'short_answer': 'Réponse courte'
        },
        'es': {
            'Вибір відповіді': 'Opción múltiple', 'Заповнити пропуск': 'Rellenar',
            'Переклад': 'Traducción', 'Аудіювання': 'Escucha', 'Говоріння': 'Hablar',
            'Згенерована': 'Ejercicio AI', 'multiple_choice': 'Opción múltiple',
            'fill_blank': 'Rellenar', 'translation': 'Traducción',
            'listening': 'Escucha', 'speaking': 'Hablar', 'ai_generated': 'Ejercicio AI',
            'essay': 'Ensayo', 'true_false': 'Verdadero/Falso', 'matching': 'Emparejamiento', 'short_answer': 'Respuesta corta'
        },
        'it': {
            'Вибір відповіді': 'Scelta multipla', 'Заповнити пропуск': 'Riempi',
            'Переклад': 'Traduzione', 'Аудіювання': 'Ascolto', 'Говоріння': 'Parlato',
            'Згенерована': 'Esercizio AI', 'multiple_choice': 'Scelta multipla',
            'fill_blank': 'Riempi', 'translation': 'Traduzione',
            'listening': 'Ascolto', 'speaking': 'Parlato', 'ai_generated': 'Esercizio AI',
            'essay': 'Saggio', 'true_false': 'Vero/Falso', 'matching': 'Abbinamento', 'short_answer': 'Risposta breve'
        },
        'pl': {
            'Вибір відповіді': 'Wielokrotny wybór', 'Заповнити пропуск': 'Luki',
            'Переклад': 'Tłumaczenie', 'Аудіювання': 'Słuchanie', 'Говоріння': 'Mówienie',
            'Згенерована': 'Zadanie AI', 'multiple_choice': 'Wielokrotny wybór',
            'fill_blank': 'Luki', 'translation': 'Tłumaczenie',
            'listening': 'Słuchanie', 'speaking': 'Mówienie', 'ai_generated': 'Zadanie AI',
            'essay': 'Esej', 'true_false': 'Prawda/Fałsz', 'matching': 'Dopasowanie', 'short_answer': 'Krótka odpowiedź'
        }
    }
    
    if lang in translations:
        return translations[lang].get(value, value)
    return value

@register.filter
def multiply(value, arg):
    """Множить значення на аргумент"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
