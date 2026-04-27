# migrations/0012_move_fields_to_studentschedule.py
from django.db import migrations, models
import django.db.models.deletion


def migrate_data_to_studentschedule(apps, schema_editor):
    Student = apps.get_model("students", "Student")
    StudentSchedule = apps.get_model("students", "StudentSchedule")
    for ss in StudentSchedule.objects.all():
        student = ss.student
        # Копируем старые значения
        ss.attendance_type = student.attendance_type
        ss.default_price = student.default_price
        ss.individual_price = student.individual_price
        ss.price_comment = student.price_comment
        ss.special_notes = student.special_notes
        ss.save()


def reverse_migration(apps, schema_editor):
    # Можно вернуть данные обратно в Student, но это не обязательно
    pass


class Migration(migrations.Migration):
    dependencies = [
        (
            "students",
            "0011_student_schedules_m2m",
        ),  # предыдущая миграция, создавшая StudentSchedule
    ]

    operations = [
        # Добавляем новые поля в StudentSchedule
        migrations.AddField(
            "studentschedule",
            "attendance_type",
            models.CharField(
                choices=[
                    ("camp", "Лагерь"),
                    ("lab", "Лаборатория"),
                    ("full_day", "Полный день"),
                ],
                default="full_day",
                max_length=20,
                verbose_name="Тип посещения",
            ),
        ),
        migrations.AddField(
            "studentschedule",
            "default_price",
            models.DecimalField(
                decimal_places=2,
                default=11400,
                max_digits=10,
                verbose_name="Базовая цена",
            ),
        ),
        migrations.AddField(
            "studentschedule",
            "individual_price",
            models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name="Индивидуальная цена",
            ),
        ),
        migrations.AddField(
            "studentschedule",
            "price_comment",
            models.CharField(
                blank=True,
                default="",
                max_length=255,
                verbose_name="Комментарий к цене",
            ),
        ),
        migrations.AddField(
            "studentschedule",
            "special_notes",
            models.TextField(blank=True, verbose_name="Особые отметки для смены"),
        ),
        # Перенос данных
        migrations.RunPython(migrate_data_to_studentschedule, reverse_migration),
        # Удаляем поля из Student
        migrations.RemoveField("student", "attendance_type"),
        migrations.RemoveField("student", "default_price"),
        migrations.RemoveField("student", "individual_price"),
        migrations.RemoveField("student", "price_comment"),
        migrations.RemoveField("student", "special_notes"),
    ]
