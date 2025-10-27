"""
Locust load testing file for Togetherly application.

Run with:
    locust -f locustfile.py --host=http://localhost:5001
"""
from locust import HttpUser, task, between
import random


class TogetherlyUser(HttpUser):
    """Simulates a user interacting with Togetherly"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts"""
        # Simulate user visiting homepage
        self.client.get("/")
    
    @task(5)
    def view_homepage(self):
        """User views the homepage"""
        self.client.get("/", name="Homepage")
    
    @task(3)
    def create_profile(self):
        """User creates a content profile"""
        profile_data = {
            "industry": random.choice([
                "restaurant", "retail", "fitness", "realtor", 
                "artisan", "coach", "nonprofit", "church"
            ]),
            "tone": random.choice(["friendly", "professional", "inspirational"]),
            "platforms": random.sample(["instagram", "facebook", "twitter"], k=2),
            "brand_keywords": ["quality", "community"],
            "niche_keywords": ["local", "sustainable"],
            "goals": ["promote", "engage"],
            "company": f"Test Company {random.randint(1, 1000)}",
            "include_images": True
        }
        
        with self.client.post(
            "/api/profile?content_version=2025.01",
            json=profile_data,
            catch_response=True,
            name="Create Profile"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to create profile: {response.status_code}")
    
    @task(2)
    def generate_content(self):
        """User generates content (most resource-intensive operation)"""
        profile_data = {
            "industry": "restaurant",
            "tone": "friendly",
            "platforms": ["instagram"],
            "brand_keywords": ["artisan"],
            "niche_keywords": ["sourdough"],
            "goals": ["promote"],
            "company": "Test Bakery",
            "include_images": False,
            "days": 3
        }
        
        with self.client.post(
            "/api/generate",
            json=profile_data,
            catch_response=True,
            name="Generate Content"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "posts" in data:
                    response.success()
                else:
                    response.failure("No posts in response")
            else:
                response.failure(f"Failed to generate content: {response.status_code}")
    
    @task(2)
    def view_account(self):
        """User views account page"""
        self.client.get("/account", name="View Account")
    
    @task(1)
    def health_check(self):
        """Load balancer health checks"""
        with self.client.get("/health", catch_response=True, name="Health Check") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class ContentGenerationUser(HttpUser):
    """Simulates users primarily generating content (high load scenario)"""
    
    wait_time = between(2, 8)
    
    @task
    def generate_content_heavy(self):
        """Simulate heavy content generation load"""
        profile_data = {
            "industry": random.choice(["restaurant", "retail", "fitness"]),
            "tone": "friendly",
            "platforms": ["instagram", "facebook"],
            "brand_keywords": ["quality"],
            "niche_keywords": ["local"],
            "goals": ["promote"],
            "company": f"Load Test Co {random.randint(1, 1000)}",
            "include_images": False,
            "days": random.randint(1, 7)
        }
        
        self.client.post("/api/generate", json=profile_data, name="Heavy Content Gen")


class ReadHeavyUser(HttpUser):
    """Simulates users browsing and reading (low resource usage)"""
    
    wait_time = between(1, 3)
    
    @task(10)
    def browse(self):
        """User browses the site"""
        self.client.get("/")
    
    @task(5)
    def view_account(self):
        """User checks account"""
        self.client.get("/account")
    
    @task(2)
    def health_check(self):
        """Health checks"""
        self.client.get("/health")


# Configure user classes for different test scenarios
# Use with: locust -f locustfile.py --host=http://localhost:5001
#
# Mixed load (default): Just run locust and select TogetherlyUser
# Content generation load: locust -f locustfile.py --host=... ContentGenerationUser
# Read-heavy load: locust -f locustfile.py --host=... ReadHeavyUser
