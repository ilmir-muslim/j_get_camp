from django.db import models

class Regulation(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название документа")
    file = models.FileField(upload_to='regulations/', verbose_name="Файл")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Регламент"
        verbose_name_plural = "Регламенты"

    def __str__(self):
        return self.title


