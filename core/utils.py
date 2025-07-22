from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    """
    Декоратор для проверки роли пользователя перед выполнением представления.

    Позволяет ограничить доступ к view только для пользователей с определёнными ролями.

    :param allowed_roles: Список допустимых ролей (строк), например: ['manager', 'admin'].
    :return: Функция-декоратор.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator


