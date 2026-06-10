ARCHIVE_DB_ALIAS = "archive_db"
LEGACY_ARCHIVE_DB_ALIAS = "archivedb"


class ArchiveRouter:
    """
    Route only the VaultArchive storage model to archive_db.
    Other models (including access logs) stay on default DB.
    """

    archive_model = ("vault", "sealedarchive")

    def _is_archive_model(self, model_or_meta) -> bool:
        app_label = model_or_meta._meta.app_label
        model_name = model_or_meta._meta.model_name
        return (app_label, model_name) == self.archive_model

    def db_for_read(self, model, **hints):
        if self._is_archive_model(model):
            return ARCHIVE_DB_ALIAS
        return None

    def db_for_write(self, model, **hints):
        if self._is_archive_model(model):
            return ARCHIVE_DB_ALIAS
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if self._is_archive_model(obj1) or self._is_archive_model(obj2):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if (app_label, model_name) == self.archive_model:
            return db in {ARCHIVE_DB_ALIAS, LEGACY_ARCHIVE_DB_ALIAS}

        if app_label == "vault":
            return db == "default"

        if db in {ARCHIVE_DB_ALIAS, LEGACY_ARCHIVE_DB_ALIAS}:
            return False

        return db == "default"
