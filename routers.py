# routers.py
class SqlServerRouter:
    def db_for_read(self, model, **hints):
        if model._meta.db_table == 'prov':
            return 'sqlserver'
        return None

    def db_for_write(self, model, **hints):
        return 'default'  # Solo escrituras en SQLite

    def allow_relation(self, obj1, obj2, **hints):
        return True  # Permitir relaciones si es necesario

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'  # Solo migraciones en SQLite