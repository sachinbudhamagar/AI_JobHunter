#!/usr/bin/env python3
"""
LinkedIn Job Scraper - Fully Working Version
"""

import json
import csv
import logging
from datetime import datetime
from collections import Counter
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.query import Query, QueryOptions
from linkedin_jobs_scraper.events import Events

# Suppress verbose logging
logging.getLogger("li").setLevel(logging.ERROR)
logging.getLogger("linkedin_jobs_scraper").setLevel(logging.ERROR)


class JobScraperHandler:
    def __init__(self):
        self.jobs = []
        self.duplicate_ids = set()
        self.stats = {"total": 0, "duplicates": 0, "errors": 0}

    def on_data(self, data):
        """Handle each job"""
        # Skip duplicates
        if data.job_id in self.duplicate_ids:
            self.stats["duplicates"] += 1
            return

        self.duplicate_ids.add(data.job_id)

        # Job data
        job = {
            "id": data.job_id,
            "title": getattr(data, "title", ""),
            "company": getattr(data, "company", ""),
            "location": getattr(data, "place", ""),
            "date": getattr(data, "date", ""),
            "url": getattr(data, "link", ""),
            "description": (getattr(data, "description", "") or "")[:500],
            "scraped_at": datetime.now().isoformat(),
        }

        self.jobs.append(job)
        self.stats["total"] += 1

        # Console output
        print(
            f"{self.stats["total"]:3}. {job["title"][:50]:50} | {job["company"][:30]:30} | {job["location"][:20]}"
        )

    def on_error(self, error):
        """Handle errors"""
        self.stats["errors"] += 1
        print(f"Error: {error}")

    def on_end(self):
        """Handle completion"""
        self.print_summary()
        self.save_results()

    def print_summary(self):
        """Print statistics"""
        print("\n" + "=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Total jobs found:   {self.stats['total']}")
        print(f"Duplicates skipped: {self.stats['duplicates']}")
        print(f"Errors:             {self.stats['errors']}")
        print("=" * 70)

        # Company breakdown
        if self.jobs:
            companies = Counter([j["company"] for j in self.jobs if j["company"]])
            print("\nTOP COMPANIES:")
            for company, count in companies.most_common(10):
                print(f"   {company[:45]:45} : {count} job(s)")

    def save_results(self):
        """Save to JSON and CSV"""
        if not self.jobs:
            print("\n No jobs to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_file = f"linkedin_jobs_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.jobs, f, indent=2, ensure_ascii=False)
        print(f"\nSaved: {json_file}")

        # Save CSV
        csv_file = f"linkedin_jobs_{timestamp}.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            # Get fieldnames from first job's keys
            fieldnames = self.jobs[0].keys()

            # Write DictWriter, header, and data
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(self.jobs)

        print(f"Saved: {csv_file}")


# Main execution
if __name__ == "__main__":
    # Get user input
    print("=" * 60)
    print("LINKEDIN JOB SCRAPER")
    print("=" * 60)

    while True:
        job_title = input("\nEnter job title to search:- ").strip()
        if not job_title:
            continue

        location = input("Enter location (default 'Nepal'):- ").strip()
        if not location:
            location = "Nepal"

        print("\n" + "-" * 60)
        print(f"Searching for: {job_title}")
        print(f"Location: {location}")
        print("-" * 60 + "\n")

        # Create handler
        scraper_handler = JobScraperHandler()

        # Setup scraper with lambda wrappers
        scraper = LinkedinScraper()
        scraper.on(Events.DATA, lambda d: scraper_handler.on_data(d))
        scraper.on(Events.ERROR, lambda e: scraper_handler.on_error(e))
        scraper.on(Events.END, lambda: scraper_handler.on_end())

        # Create query with user input
        queries = [
            Query(query=job_title, options=QueryOptions(locations=[location], limit=27))
        ]

        # Run scraper
        try:
            scraper.run(queries)
        except Exception as e:
            print(f"\n Error: {e}")

        break
