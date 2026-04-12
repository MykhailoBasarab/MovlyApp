from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Отримати елемент зі словника за ключем"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def premium_label(value, lang="uk"):
    """Перетворює назви вправ на мову курсу"""
    translations = {
        "en": {
            "Вибір правильної відповіді": "Master Quiz",
            "Заповни пропуски": "Fill the Blanks",
            "Майстер перекладу": "Translation Master",
            "Аудіо-аналіз": "Listening Mastery",
            "Мовна практика": "Speaking Quest",
            "Майстер-квест": "Elite Quest",
            "Логічний вибір": "Logic Test",
            "Виклик зіставлення": "Matching Challenge",
            "Експрес-відповідь": "Express Answer",
            "Творче есе": "Creative Essay",
            "multiple_choice": "Master Quiz",
            "fill_blank": "Fill the Blanks",
            "translation": "Translation Master",
            "listening": "Listening Mastery",
            "speaking": "Speaking Quest",
            "ai_generated": "Elite Quest",
            "essay": "Premium Essay",
            "true_false": "Logic Test",
            "matching": "Connection Challenge",
            "short_answer": "Express Answer",
        },
        "de": {
            "Вибір правильної відповіді": "Quiz-Meister",
            "Заповни пропуски": "Lückentext-Pro",
            "Майстер перекладу": "Übersetzungs-Profi",
            "Аудіо-аналіз": "Hörverstehen",
            "Мовна практика": "Sprachpraxis",
            "Майстер-квест": "Elite-Herausforderung",
            "Логічний вибір": "Logik-Test",
            "Виклик зіставлення": "Zuordnungs-Challenge",
            "Експрес-відповідь": "Kurzantwort",
            "Творче есе": "Kreatives Essay",
            "multiple_choice": "Quiz-Meister",
            "fill_blank": "Lückentext-Pro",
            "translation": "Übersetzungs-Profi",
            "listening": "Hörverstehen",
            "speaking": "Sprachpraxis",
            "ai_generated": "Elite-Herausforderung",
            "essay": "Premium Aufsatz",
            "true_false": "Richtig/Falsch",
            "matching": "Zuordnung",
            "short_answer": "Kurzantwort",
        },
        "fr": {
            "Вибір правильної відповіді": "Maître du Quiz",
            "Заповни пропуски": "Texte à trous",
            "Майстер перекладу": "Expert en Traduction",
            "Аудіо-аналіз": "Analyse Audio",
            "Мовна практика": "Pratique Orale",
            "Майстер-квест": "Quête Élite",
            "Логічний вибір": "Test de Logique",
            "Виклик зіставлення": "Défi de Correspondance",
            "Експрес-відповідь": "Réponse Rapide",
            "Творче есе": "Essai Créatif",
            "multiple_choice": "Maître du Quiz",
            "fill_blank": "Texte à trous",
            "translation": "Expert en Traduction",
            "listening": "Analyse Audio",
            "speaking": "Pratique Orale",
            "ai_generated": "Quête Élite",
            "essay": "Rédaction Premium",
            "true_false": "Vrai/Faux",
            "matching": "Correspondance",
            "short_answer": "Réponse Rapide",
        },
        "es": {
            "Вибір правильної відповіді": "Maestro del Quiz",
            "Заповни пропуски": "Rellenar Huecos",
            "Майстер перекладу": "Experto en Traducción",
            "Аудіо-аналіз": "Análisis de Audio",
            "Мовна практика": "Práctica de Habla",
            "Майстер-квест": "Búsqueda Élite",
            "Логічний вибір": "Prueba de Lógica",
            "Виклик зіставлення": "Desafío de Emparejamiento",
            "Експрес-відповідь": "Respuesta Corta",
            "Творче есе": "Ensayo Creativo",
            "multiple_choice": "Maestro del Quiz",
            "fill_blank": "Rellenar Huecos",
            "translation": "Experto en Traducción",
            "listening": "Análisis de Audio",
            "speaking": "Práctica de Habla",
            "ai_generated": "Búsqueda Élite",
            "essay": "Ensayo Premium",
            "true_false": "Verdadero/Falso",
            "matching": "Emparejamiento",
            "short_answer": "Respuesta Corta",
        },
        "it": {
            "Вибір правильної відповіді": "Maestro del Quiz",
            "Заповни пропуски": "Riempi i Vuoti",
            "Майстер перекладу": "Esperto in Traduzione",
            "Аудіо-аналіз": "Analisi Audio",
            "Мовна практика": "Pratica Orale",
            "Майстер-квест": "Sfida Élite",
            "Логічний вибір": "Test di Logica",
            "Виклик зіставлення": "Sfida di Abbinamento",
            "Експрес-відповідь": "Risposta Rapida",
            "Творче есе": "Saggio Creativo",
            "multiple_choice": "Maestro del Quiz",
            "fill_blank": "Riempi i Vuoti",
            "translation": "Esperto in Traduzione",
            "listening": "Analisi Audio",
            "speaking": "Pratica Orale",
            "ai_generated": "Sfida Élite",
            "essay": "Saggio Premium",
            "true_false": "Vero/Falso",
            "matching": "Abbinamento",
            "short_answer": "Risposta Rapida",
        },
        "pl": {
            "Вибір правильної відповіді": "Mistrz Quizu",
            "Заповни пропуски": "Uzupełnij Luki",
            "Майстер перекладу": "Mistrz Tłumaczenia",
            "Аудіо-аналіз": "Analiza Audio",
            "Мовна практика": "Praktyka Językowa",
            "Майстер-квест": "Wyzwanie Élite",
            "Логічний вибір": "Test Logiczny",
            "Виклик зіставлення": "Wyzwanie Dopasowania",
            "Експрес-відповідь": "Szybka Odpowiedź",
            "Творче есе": "Esej Kreatywny",
            "multiple_choice": "Mistrz Quizu",
            "fill_blank": "Uzupełnij Luki",
            "translation": "Mistrz Tłumaczenia",
            "listening": "Analiza Audio",
            "speaking": "Praktyka Językowa",
            "ai_generated": "Wyzwanie Élite",
            "essay": "Esej Premium",
            "true_false": "Prawda/Fałsz",
            "matching": "Dopasowanie",
            "short_answer": "Szybka Odpowiedź",
        },
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


@register.filter
def to_flag_url(lang_code):
    """Перетворює код мови в URL SVG прапора"""
    if not lang_code:
        return ""
    
    # Map common lang codes to their primary flag equivalent (ISO-3166-1 alpha-2)
    mapping = {
        'en': 'gb',
        'uk': 'ua',
        'ja': 'jp',
        'ko': 'kr',
        'zh': 'cn',
        'pl': 'pl',
        'de': 'de',
        'fr': 'fr',
        'es': 'es',
        'it': 'it',
    }
    
    input_code = str(lang_code).lower()
    code = mapping.get(input_code, input_code)
    
    return f"https://flagicons.lipis.dev/flags/4x3/{code}.svg"
