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
            
    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Dict:
        """Make HTTP request with error handling"""
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    raise APIError(f"API request failed with status {response.status}")
                return await response.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection error: {str(e)}")
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response")


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

    async def search_all_providers(
        self, 
        skills: List[str], 
        limit_per_provider: int = 10,
        sort_by: str = None,
        filters: Dict = None,
        price_range: Optional[Tuple[float, float]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Search courses across all providers with sorting and filtering.
        
        Args:
            skills: List of skills to search for
            limit_per_provider: Maximum number of results per provider
            sort_by: Sort results by 'price', 'rating', or 'reviews'
            filters: Dictionary of filters (e.g., {'language': 'English', 'certificate': True})
            price_range: Optional tuple of (min_price, max_price)
        """
        async with self.coursera, self.udemy, self.edx:
            tasks = [
                self._safe_provider_search(provider, skills, limit_per_provider)
                for provider in [self.coursera, self.udemy, self.edx]
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle errors
            processed_results = {}
            for provider, result in zip(['coursera', 'udemy', 'edx'], results):
                if isinstance(result, Exception):
                    processed_results[provider] = {'error': str(result), 'courses': []}
                else:
                    processed_results[provider] = {'error': None, 'courses': result}

            # Apply filters and sorting
            for provider in processed_results:
                if processed_results[provider]['error'] is None:
                    courses = processed_results[provider]['courses']
                    courses = self._apply_filters(courses, filters, price_range)
                    courses = self._sort_courses(courses, sort_by)
                    processed_results[provider]['courses'] = courses

            return processed_results

    async def _safe_provider_search(self, provider, skills, limit):
        """Safely execute provider search with timeout"""
        try:
            return await asyncio.wait_for(
                provider.search_courses(skills, limit),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request timed out")

    def _apply_filters(self, courses: List[Dict], filters: Dict, price_range: Optional[Tuple[float, float]]) -> List[Dict]:
        """Apply filters to course results"""
        if not filters and not price_range:
            return courses

        filtered_courses = courses
        if filters:
            for key, value in filters.items():
                filtered_courses = [
                    course for course in filtered_courses
                    if course.get(key) == value
                ]

        if price_range:
            min_price, max_price = price_range
            filtered_courses = [
                course for course in filtered_courses
                if self._get_numeric_price(course.get('price', 0)) >= min_price
                and self._get_numeric_price(course.get('price', 0)) <= max_price
            ]

        return filtered_courses

    def _sort_courses(self, courses: List[Dict], sort_by: Optional[str]) -> List[Dict]:
        """Sort courses based on specified criteria"""
        if not sort_by:
            return courses

        def get_sort_key(course):
            if sort_by == 'price':
                return self._get_numeric_price(course.get('price', 0))
            elif sort_by == 'rating':
                return float(course.get('rating', 0))
            elif sort_by == 'reviews':
                return int(course.get('reviews', 0))
            return 0

        return sorted(courses, key=get_sort_key, reverse=True)

    def _get_numeric_price(self, price) -> float:
        """Convert price string to numeric value"""
        if isinstance(price, (int, float)):
            return float(price)
        if isinstance(price, str):
            try:
                return float(''.join(filter(str.isdigit, price)))
            except ValueError:
                return 0.0
        return 0.0

# Custom exceptions
class APIError(Exception):
    pass

class RateLimitError(Exception):
    pass


