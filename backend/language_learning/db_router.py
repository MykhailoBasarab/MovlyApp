"""
Database router для розподілу моделей між базами даних
"""


class DatabaseRouter:
    """
    Router для визначення яку базу даних використовувати для кожної моделі
    """

    route_app_labels = {"courses", "users", "tests"}
    analytics_app_labels = {"ai_services"}

    def db_for_read(self, model, **hints):
        """Читання з основної бази даних"""
        if model._meta.app_label in self.analytics_app_labels:
            return "analytics"
        return "default"

    def db_for_write(self, model, **hints):
        """Запис в основну базу даних"""
        if model._meta.app_label in self.analytics_app_labels:
            return "analytics"
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """Дозволити зв'язки між моделями"""
        db_set = {"default", "analytics"}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Визначити які моделі мігрувати в яку базу"""
        if app_label in self.analytics_app_labels:
            return db == "analytics"
        elif app_label in self.route_app_labels:
            return db == "default"
        return None
