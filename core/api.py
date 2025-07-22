from ninja import Router
from django.contrib.auth import authenticate, login, logout
from .schemas import AuthSchema

router = Router(tags=["Auth"])

@router.post("/login/", response={200: dict, 401: dict})
def user_login(request, data: AuthSchema):
    user = authenticate(username=data.username, password=data.password)
    if user is not None:
        login(request, user)
        return 200, {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }
    return 401, {"success": False, "message": "Invalid credentials"}

@router.post("/logout/", response={200: dict})  # <-- без auth=django_auth!
def user_logout(request):
    logout(request)
    return {"success": True}
