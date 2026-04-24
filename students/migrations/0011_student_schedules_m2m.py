# Generated manually
from django.db import migrations, models
import django.db.models.deletion


def migrate_schedule_to_schedules(apps, schema_editor):
    Student = apps.get_model("students", "Student")
    StudentSchedule = apps.get_model("students", "StudentSchedule")
    for student in Student.objects.exclude(schedule__isnull=True):
        StudentSchedule.objects.create(
            student=student,
            schedule=student.schedule,
        )


def reverse_migrate(apps, schema_editor):
    StudentSchedule = apps.get_model("students", "StudentSchedule")
    Student = apps.get_model("students", "Student")
    for link in StudentSchedule.objects.all():
        student = link.student
        student.schedule = link.schedule
        student.save()


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0010_student_special_notes"),
        ("schedule", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentSchedule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "added_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата добавления"
                    ),
                ),
                (
                    "schedule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="schedule.schedule",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="students.student",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ученик в смене",
                "verbose_name_plural": "Ученики в сменах",
                "unique_together": {("student", "schedule")},
            },
        ),
        migrations.AddField(
            model_name="student",
            name="schedules",
            field=models.ManyToManyField(
                through="students.StudentSchedule",
                to="schedule.schedule",
                related_name="students",
                verbose_name="Смены",
            ),
        ),
        migrations.RunPython(migrate_schedule_to_schedules, reverse_migrate),
        migrations.RemoveField(
            model_name="student",
            name="schedule",
        ),
    ]
