import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'language_learning.settings')
django.setup()

from courses.models import Course, Lesson, Exercise

def update_french():
    print("Updating French lessons...")

    fr_course = Course.objects.filter(language="fr").first()
    if fr_course:
        lesson, created = Lesson.objects.get_or_create(
            course=fr_course,
            title="Surviving in a French Café",
            order=1,
            defaults={"description": "Learn how to order coffee and croissants like a local."}
        )
        lesson.content = """
# ☕️ Surviving in a French Café

Ordering coffee in France is more than just a transaction; it's a social ritual. Here is how to do it right.

### 🥖 Essential Phrases

| French | English |
| :--- | :--- |
| **Bonjour !** | Hello! (Always start with this) |
| **Je voudrais...** | I would like... |
| **Un café, s'il vous plaît.** | An espresso, please. |
| **Un café au lait.** | Coffee with milk. |
| **Un croissant.** | A croissant. |
| **L'addition, s'il vous plaît.** | The check, please. |

---

### 💡 Cultural Tips

1.  **Always say "Bonjour":** It is considered very rude to start an order without a greeting.
2.  **Un café:** If you just say "un café", you will get a small, strong espresso.
3.  **S'il vous plaît:** Use this constantly. Politeness is key in French culture.

---
### 🛠 Practice Dialogue

**Serveur:** Bonjour ! Vous désirez ?
**Vous:** Bonjour ! Je voudrais un café au lait et два croissants, s'il vous plaît.
**Serveur:** Très bien. Autre chose ?
**Vous:** Non, merci. C'est tout.
        """
        lesson.save()
        print(f"Updated French lesson: {lesson.title}")

if __name__ == "__main__":
    update_french()
