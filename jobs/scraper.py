# jobs/scraper.py
import logging
from datetime import datetime
from collections import Counter
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.query import Query, QueryOptions
from linkedin_jobs_scraper.events import Events

logging.getLogger("li").setLevel(logging.ERROR)
logging.getLogger("linkedin_jobs_scraper").setLevel(logging.ERROR)


class LinkedInJobScraper:
    """Scraper for LinkedIn jobs"""

    def __init__(self):
        self.jobs = []
        self.duplicate_ids = set()
        self.stats = {"total": 0, "duplicates": 0, "errors": 0}

    def on_data(self, data):
        """Handle each job"""
        try:
            # Trying different possible field names for job ID
            job_id = None
            if hasattr(data, "job_id"):
                job_id = data.job_id
            elif hasattr(data, "id"):
                job_id = data.id
            elif hasattr(data, "jobId"):
                job_id = data.jobId
            else:
                # Generate a unique ID if none exists
                job_id = f"job_{datetime.now().timestamp()}_{len(self.jobs)}"

            # Skip duplicates
            if job_id in self.duplicate_ids:
                self.stats["duplicates"] += 1
                return

            self.duplicate_ids.add(job_id)

            # Extract job data
            title = (
                getattr(data, "title", None)
                or getattr(data, "name", None)
                or "No Title"
            )
            company = (
                getattr(data, "company", None)
                or getattr(data, "company_name", None)
                or "Unknown"
            )
            location = (
                getattr(data, "place", None)
                or getattr(data, "location", None)
                or "Unknown"
            )
            url = getattr(data, "link", None) or getattr(data, "url", None) or ""
            description = (
                getattr(data, "description", None)
                or getattr(data, "job_description", None)
                or ""
            )
            date = (
                getattr(data, "date", None) or getattr(data, "posted_date", None) or ""
            )

            # Dictionary with field names
            job = {
                "job_id": str(job_id),
                "title": title[:200],
                "company": company[:200],
                "location": location[:200],
                "url": url,
                "description": description[:500],
                "date": date[:50],
            }

            self.jobs.append(job)
            self.stats["total"] += 1
            print(
                f"{self.stats['total']:3}. {job['title'][:50]:50} | {job['company'][:30]:30}"
            )

        except Exception as e:
            self.stats["errors"] += 1
            print(f"Error processing job: {e}")

    def on_error(self, error):
        """Handle errors"""
        self.stats["errors"] += 1
        print(f"Error: {error}")

    def on_end(self):
        """Handle completion"""
        self.print_summary()

    def print_summary(self):
        """Print statistics"""
        print("\n" + "=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Total jobs found:   {self.stats['total']}")
        print(f"Duplicates skipped: {self.stats['duplicates']}")
        print(f"Errors:             {self.stats['errors']}")
        print("=" * 70)

        if self.jobs:
            companies = Counter([j["company"] for j in self.jobs if j["company"]])
            print("\nTOP COMPANIES:")
            for company, count in companies.most_common(10):
                print(f"   {company[:45]:45} : {count} job(s)")

    def scrape(self, job_title, location="Nepal", limit=27):
        """Main method to run the scraper"""
        print(f"\nStarting scrape for: {job_title} in {location}")

        # Reset state
        self.jobs = []
        self.duplicate_ids = set()
        self.stats = {"total": 0, "duplicates": 0, "errors": 0}

        # scraper instance
        scraper = LinkedinScraper()

        scraper.on(Events.DATA, lambda data: self.on_data(data))
        scraper.on(Events.ERROR, lambda error: self.on_error(error))
        scraper.on(Events.END, lambda: self.on_end())

        # Create query
        queries = [
            Query(
                query=job_title, options=QueryOptions(locations=[location], limit=limit)
            )
        ]

        # Run scraper
        try:
            scraper.run(queries)
            print(f"\nScraping complete. Found {len(self.jobs)} jobs")
            return self.jobs
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback

            traceback.print_exc()
            return []
