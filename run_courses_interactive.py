import asyncio
from course_provider_integrations_v7 import CourseAggregator
import json
from pprint import pprint

API_KEYS = {
    'coursera': 'your_coursera_api_key',
    'udemy': 'your_udemy_api_key',
    'edx': 'your_edx_api_key'
}

async def main():
    # Initialize the aggregator
    aggregator = CourseAggregator(API_KEYS)
    
    # Get user input
    print("Enter skills to search for (comma-separated):")
    skills = [skill.strip() for skill in input().split(',')]
    
    print("\nEnter maximum price (press Enter for no limit):")
    max_price = input()
    price_range = (0, float(max_price)) if max_price else None
    
    print("\nSort by (rating/price/reviews) or press Enter for no sorting:")
    sort_by = input() or None
    
    print("\nFilter by language (press Enter for all languages):")
    language = input() or None
    
    filters = {}
    if language:
        filters['language'] = language
    
    search_params = {
        'skills': skills,
        'limit_per_provider': 5,
        'sort_by': sort_by,
        'filters': filters if filters else None,
        'price_range': price_range
    }
    
    try:
        print("\nSearching courses...")
        results = await aggregator.search_all_providers(**search_params)
        
        print("\n=== Course Search Results ===\n")
        
        for provider, data in results.items():
            print(f"\n{provider.upper()}:")
            if data['error']:
                print(f"Error: {data['error']}")
            else:
                print(f"Found {len(data['courses'])} courses:")
                for course in data['courses']:
                    print("\n---")
                    print(f"Title: {course['title']}")
                    print(f"Price: {course['price']}")
                    print(f"URL: {course['url']}")
                    if 'rating' in course:
                        print(f"Rating: {course['rating']}")
                    print(f"Description: {course['description'][:200]}...")
                    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 