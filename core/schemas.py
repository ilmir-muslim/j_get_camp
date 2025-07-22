from ninja import Schema

class AuthSchema(Schema):
    username: str
    password: str

class UserSchema(Schema):
    id: int
    username: str
    role: str