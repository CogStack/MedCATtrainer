from django.db import models

class Filter(models.Model):
    name = models.CharField(max_length=150)
    value = models.IntegerField(default=1)
    acc = models.FloatField(default=0)

    def __str__(self):
        return self.name


class Value(models.Model):
    name = models.CharField(max_length=150)
    value = models.IntegerField(default=1)

    def __str__(self):
        return self.name


class Task(models.Model):
    name = models.CharField(max_length=150)
    values = models.ManyToManyField(Value)
    cntx_size = models.IntegerField(default=7)

    def __str__(self):
        return self.name


class UseCase(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(default="")
    cuis = models.TextField(default="")
    tuis = models.TextField(default="")
    tokens = models.TextField(default="")
    cntx_tokens = models.TextField(default="")
    filters = models.ManyToManyField(Filter)
    other = models.TextField(default="")
    tasks = models.ManyToManyField(Task)
    type = models.CharField(max_length=50, default='all')
    folder = models.CharField(max_length=50, default='train')

    def __str__(self):
        return self.title

