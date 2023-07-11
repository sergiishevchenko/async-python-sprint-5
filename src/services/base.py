from src.models.models import File, Directory, User
from src.schemes.user import UserRegister

from .directory import RepositoryDirectoryDB
from .file import RepositoryFileDB
from .user import RepositoryUserDB


class RepositoryDirectory(RepositoryDirectoryDB[File]):
    pass


class RepositoryFile(RepositoryFileDB[File]):
    pass


class RepositoryUser(RepositoryUserDB[User, UserRegister]):
    pass


directory_crud = RepositoryDirectory(Directory)
file_crud = RepositoryFile(File)
user_crud = RepositoryUser(User)

