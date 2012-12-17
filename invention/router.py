class EveDBRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'eve_db':
            return 'eve'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'eve_db':
            return 'eve'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'eve_db' and obj2._meta.app_label == 'eve_db':
            return True
        elif obj1._meta.app_label == 'eve_db' or obj2._meta.app_label == 'eve_db':
            return False
        return None

    def allow_syncdb(self, db, model):
        if db == 'eve':
            return False
        elif model._meta.app_label == 'eve_db':
            return False
        return None
