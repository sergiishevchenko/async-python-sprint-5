from passlib.context import CryptContext


crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, password):
    return crypt_context.verify(plain_password, password)


def get_hashed_password(password):
    return crypt_context.hash(password)
