from .settings import *  # noqa: F401,F403


DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_default.sqlite3",
    },
    "archive_db": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_archive.sqlite3",
    },
    # Compat alias.
    "archivedb": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_archive.sqlite3",
    },
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
