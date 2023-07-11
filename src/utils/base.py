from src.core.settings import settings


def get_full_path(path: str):
    return settings.files_path + path


