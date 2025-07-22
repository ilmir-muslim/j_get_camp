from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    address = models.TextField(blank=True, verbose_name='Адрес')

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"

