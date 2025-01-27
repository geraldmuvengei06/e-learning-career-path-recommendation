import aiohttp
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import json
from urllib.parse import urlencode
import hashlib
import hmac
import time

class CourseProviderBase:
    def __init__(self, api_key: str, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

class CourseraAPI(CourseProviderBase):
    BASE_URL = "https://api.coursera.org/api/courses.v1"
    
    async def search_courses(self, skills: List[str], limit: int = 20) -> List[Dict]:
        """Search Coursera courses based on skills."""
        query_params = {
            "q": " OR ".join(skills),
            "limit": limit,
            "fields": "name,slug,description,workload,primaryLanguages,subtitleLanguages,partnerLogo,certificates,startDate,closeDate,courseType",
            "includes": "partnerIds,instructorIds"
        }
        
        async with self.session.get(f"{self.BASE_URL}/search", params=query_params) as response:
            data = await response.json()
            return await self._process_coursera_results(data['elements'])
            
    async def _process_coursera_results(self, courses: List[Dict]) -> List[Dict]:
        """Process and standardize Coursera course data."""
        processed_courses = []
        for course in courses:
            processed_courses.append({
                "provider": "Coursera",
                "title": course['name'],
                "description": course['description'],
                "url": f"https://www.coursera.org/learn/{course['slug']}",
                "image_url": course.get('partnerLogo'),
                "duration": course.get('workload', 'Flexible'),
                "language": course.get('primaryLanguages', ['English'])[0],
                "certificate": bool(course.get('certificates')),
                "start_date": course.get('startDate', 'Self-paced'),
                "price": "Free to audit, Certificate available",
                "provider_id": course['id']
            })
        return processed_courses

class UdemyAPI(CourseProviderBase):
    BASE_URL = "https://www.udemy.com/api-2.0"
    
    async def search_courses(self, skills: List[str], limit: int = 20) -> List[Dict]:
        """Search Udemy courses based on skills."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        query_params = {
            "search": " OR ".join(skills),
            "page_size": limit,
            "ordering": "relevance",
            "fields[course]": "title,headline,url,image_480x270,price,published_title,avg_rating,num_reviews"
        }
        
        async with self.session.get(
            f"{self.BASE_URL}/courses",
            headers=headers,
            params=query_params
        ) as response:
            data = await response.json()
            return await self._process_udemy_results(data['results'])
            
    async def _process_udemy_results(self, courses: List[Dict]) -> List[Dict]:
        """Process and standardize Udemy course data."""
        processed_courses = []
        for course in courses:
            processed_courses.append({
                "provider": "Udemy",
                "title": course['title'],
                "description": course['headline'],
                "url": course['url'],
                "image_url": course['image_480x270'],
                "price": f"${course['price']}",
                "rating": course['avg_rating'],
                "reviews": course['num_reviews'],
                "provider_id": course['id']
            })
        return processed_courses

class EdXAPI(CourseProviderBase):
    BASE_URL = "https://api.edx.org/catalog/v1"
    
    async def search_courses(self, skills: List[str], limit: int = 20) -> List[Dict]:
        """Search EdX courses based on skills."""
        headers = {
            "X-Edx-Api-Key": self.api_key
        }
        
        query_params = {
            "q": " OR ".join(skills),
            "limit": limit,
            "fields": "title,short_description,marketing_url,image_url,price,start,end,pacing_type"
        }
        
        async with self.session.get(
            f"{self.BASE_URL}/courses/",
            headers=headers,
            params=query_params
        ) as response:
            data = await response.json()
            return await self._process_edx_results(data['results'])
            
    async def _process_edx_results(self, courses: List[Dict]) -> List[Dict]:
        """Process and standardize EdX course data."""
        processed_courses = []
        for course in courses:
            processed_courses.append({
                "provider": "EdX",
                "title": course['title'],
                "description": course['short_description'],
                "url": course['marketing_url'],
                "image_url": course['image_url'],
                "price": course.get('price', 'Free to audit, Certificate available'),
                "start_date": course.get('start', 'Self-paced'),
                "pacing": course.get('pacing_type', 'Self-paced'),
                "provider_id": course['id']
            })
        return processed_courses

class CourseAggregator:
    def __init__(self, api_keys: Dict[str, str]):
        self.coursera = CourseraAPI(api_keys['coursera'])
        self.udemy = UdemyAPI(api_keys['udemy'])
        self.edx = EdXAPI(api_keys['edx'])
        
    async def search_all_providers(self, skills: List[str], limit_per_provider: int = 10) -> Dict[str, List[Dict]]:
        """Search courses across all providers."""
        async with self.coursera, self.udemy, self.edx:
            tasks = [
                self.coursera.search_courses(skills, limit_per_provider),
                self.udemy.search_courses(skills, limit_per_provider),
                self.edx.search_courses(skills, limit_per_provider)
            ]
            
            results = await asyncio.gather(*tasks)
            
            return {
                "coursera": results[0],
                "udemy": results[1],
                "edx": results[2]
            }
