# jobs/views.py
import json
import csv
import logging
from datetime import datetime
from collections import Counter
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from .models import Jobs
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.query import Query, QueryOptions
from linkedin_jobs_scraper.events import Events

logging.getLogger("li").setLevel(logging.ERROR)
logging.getLogger("linkedin_jobs_scraper").setLevel(logging.ERROR)


# Funtion to display all jobs
def job_list(request):
    """Display all scraped jobs"""
    all_jobs = Jobs.objects.all().order_by("-scraped_at")  # Newest first
    return render(request, "jobs/list.html", {"jobs": all_jobs})


class JobScraperHandler:
    def __init__(self):
        self.jobs = []
        self.duplicate_ids = set()
        self.stats = {"total": 0, "duplicates": 0, "errors": 0}

    def on_data(self, data):
        """Handle each job"""
        if data.job_id in self.duplicate_ids:
            self.stats["duplicates"] += 1
            return

        self.duplicate_ids.add(data.job_id)

        job = {
            "job_id": data.job_id,
            "title": getattr(data, "title", ""),
            "company": getattr(data, "company", ""),
            "location": getattr(data, "place", ""),
            "date": getattr(data, "date", ""),
            "url": getattr(data, "link", ""),
            "description": (getattr(data, "description", "") or "")[:500],
        }

        self.jobs.append(job)
        self.stats["total"] += 1
        print(
            f"{self.stats['total']:3}. {job['title'][:50]:50} | {job['company'][:30]:30}"
        )

    def on_error(self, error):
        self.stats["errors"] += 1
        print(f"Error: {error}")

    def on_end(self):
        self.print_summary()

    def print_summary(self):
        print("\n" + "=" * 70)
        print(f"Total jobs found: {self.stats['total']}")
        print(f"Duplicates: {self.stats['duplicates']}")
        print(f"Errors: {self.stats['errors']}")
        print("=" * 70)

    def scrape(self, job_title, location="Nepal", limit=27):
        """Run the scraper"""
        scraper = LinkedinScraper()
        scraper.on(Events.DATA, lambda d: self.on_data(d))
        scraper.on(Events.ERROR, lambda e: self.on_error(e))
        scraper.on(Events.END, lambda: self.on_end())

        queries = [
            Query(
                query=job_title, options=QueryOptions(locations=[location], limit=limit)
            )
        ]

        try:
            scraper.run(queries)
            return self.jobs
        except Exception as e:
            print(f"Error: {e}")
            return []


# Scraping view for web interface
class ScrapeJobsView(View):
    def get(self, request):
        return render(request, "jobs/scrape_form.html")

    def post(self, request):
        job_title = request.POST.get("job_title", "").strip()
        location = request.POST.get("location", "Nepal").strip()

        if not job_title:
            messages.error(request, "Please enter a job title")
            return render(request, "jobs/scrape_form.html")

        # Run scraper
        scraper = JobScraperHandler()
        scraped_jobs = scraper.scrape(job_title, location)

        # Save to database
        jobs_saved = 0
        for job_data in scraped_jobs:
            obj, created = Jobs.objects.get_or_create(
                job_id=job_data["job_id"],
                defaults={
                    "title": job_data.get("title", ""),
                    "company": job_data.get("company", ""),
                    "location": job_data.get("location", ""),
                    "url": job_data.get("url", ""),
                    "description": job_data.get("description", ""),
                    "date": job_data.get("date", ""),
                },
            )
            if created:
                jobs_saved += 1

        messages.success(request, f"Saved {jobs_saved} new jobs!")
        return redirect("job_list")
