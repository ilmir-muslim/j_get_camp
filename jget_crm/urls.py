from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from ninja import NinjaAPI

# Создаём основной API-объект
api = NinjaAPI(title="J-GET CAMP API", csrf=False)

# Импортируем все API-роутеры
from core.api import router as core_router
from students.api import router as students_router
from employees.api import router as employees_router
from leads.api import router as leads_router
from payroll.api import router as payroll_router
from branches.api import router as branches_router
from education.api import router as education_router
from schedule.api import router as schedule_router

# Подключаем роутеры 
api.add_router("", core_router) 
api.add_router("students/", students_router)
api.add_router("employees/", employees_router)
api.add_router("leads/", leads_router)
api.add_router("payroll/", payroll_router)
api.add_router("branches/", branches_router)
api.add_router("education/", education_router)
api.add_router("schedule/", schedule_router)

# Основные URL-паттерны
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("schedule/", include("schedule.urls")),
    path("employees/", include("employees.urls")),
    path("students/", include("students.urls")),
    path("leads/", include("leads.urls")),
    path("payroll/", include("payroll.urls")),
    path("education/", include("education.urls")),
    path("branches/", include("branches.urls")),

    path("login/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    path("api/", api.urls),
]

# Статические файлы
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
