from django.db import models


# Create your models here.
class Jobs(models.Model):
    job_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    date = models.CharField(max_length=50, blank=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

    class Meta:
        ordering = ["-scraped_at"]
