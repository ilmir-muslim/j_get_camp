from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import Lower, Trim
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse

from schedule.templatetags.schedule_extras import romanize
from .models import Student, Squad


@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    list_display = ["name", "get_roman_name", "leader", "schedule", "student_count"]
    list_filter = ["schedule", "schedule__branch"]
    search_fields = ["name", "leader__full_name"]

    def get_roman_name(self, obj):
        return romanize(obj.name)

    get_roman_name.short_description = "Номер (римский)"

    def student_count(self, obj):
        return obj.students.count()

    student_count.short_description = "Количество учеников"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    change_list_template = "admin/students/student/change_list.html"
    list_display = ["full_name", "phone", "parent_name", "display_squads"]
    search_fields = ["full_name", "phone"]

    def display_squads(self, obj):
        return ", ".join(str(s.id) for s in obj.schedules.all())

    display_squads.short_description = "Смены (ID)"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "duplicates/",
                self.admin_site.admin_view(self.duplicate_check_view),
                name="students_student_duplicates",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["duplicate_check_url"] = reverse(
            "admin:students_student_duplicates"
        )
        return super().changelist_view(request, extra_context=extra_context)

    def duplicate_check_view(self, request):
        # Нормализация для поиска дубликатов
        duplicates = (
            Student.objects.annotate(normalized_name=Lower(Trim("full_name")))
            .values("normalized_name")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates:
            messages.info(request, "Дубликаты не найдены.")
            return HttpResponseRedirect("../")

        duplicate_groups = []
        for dup in duplicates:
            students = Student.objects.filter(
                full_name__iexact=dup["normalized_name"].strip()
            ).order_by("id")
            duplicate_groups.append(list(students))

        if request.method == "POST":
            with transaction.atomic():
                for group in duplicate_groups:
                    master_id = request.POST.get(f"master_{group[0].id}")
                    if not master_id:
                        continue
                    try:
                        master = Student.objects.get(id=master_id)
                    except Student.DoesNotExist:
                        continue

                    # Остальные записи — дубликаты
                    for duplicate in group:
                        if duplicate.id == master.id:
                            continue
                        self.merge_students(master, duplicate)
            messages.success(request, "Слияние дубликатов выполнено успешно.")
            return HttpResponseRedirect("../")

        context = {
            "title": "Проверка дубликатов учеников",
            "duplicate_groups": duplicate_groups,
            "opts": self.model._meta,
        }
        return render(request, "admin/students/student/merge_duplicates.html", context)

    def merge_students(self, master, duplicate):
        """
        Переносит все данные от duplicate к master и удаляет duplicate.
        """
        # 1. Перенос ManyToMany смен (StudentSchedule)
        for ss in duplicate.studentschedule_set.all():
            # Если у master ещё нет такой смены, создаём копию
            if not master.studentschedule_set.filter(schedule=ss.schedule).exists():
                ss.student = master
                ss.id = None  # создаст новую запись
                ss.save()
            # Если уже есть, просто удаляем связь дубликата (ниже)
        duplicate.studentschedule_set.all().delete()

        # 2. Посещаемость (Attendance)
        for att in duplicate.attendance_set.all():
            try:
                master_att = master.attendance_set.get(date=att.date)
                # Объединяем статусы: если хоть один раз присутствовал – present,
                # если хоть один раз по уважительной – excused
                master_att.present = master_att.present or att.present
                master_att.excused = master_att.excused or att.excused
                master_att.save()
            except master.attendance_set.model.DoesNotExist:
                att.student = master
                att.id = None
                att.save()
        duplicate.attendance_set.all().delete()

        # 3. Платежи (Payment)
        duplicate.payments.all().update(student=master)

        # 4. Операции по балансу (Balance)
        duplicate.balance_operations.all().update(student=master)

        # 5. Отряд (squad) – переносим, только если у master не задан
        if not master.squad and duplicate.squad:
            master.squad = duplicate.squad
            master.save(update_fields=["squad"])

        # Удаляем дубликат
        duplicate.delete()
