from django.urls import path
from . import views

urlpatterns = [
    # view all jobs
    path("", views.job_list, name="job_list"),
    # Scrape new jobs
    path("scrape/", views.ScrapeJobsView.as_view(), name="scrape"),
]
