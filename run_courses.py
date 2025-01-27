import asyncio
from course_provider_integrations_v7 import CourseAggregator
import json
from pprint import pprint

# Your API keys - replace with actual keys
API_KEYS = {
    'coursera': 'your_coursera_api_key',
    'udemy': 'your_udemy_api_key',
    'edx': 'your_edx_api_key'
}

async def main():
    # Initialize the aggregator
    aggregator = CourseAggregator(API_KEYS)
    
    # Define search parameters
    search_params = {
        'skills': ['python', 'machine learning'],
        'limit_per_provider': 5,
        'sort_by': 'rating',
        'filters': {'language': 'English'},
        'price_range': (0, 100)
    }
    
    try:
        # Search for courses
        results = await aggregator.search_all_providers(**search_params)
        
        # Print results nicely
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
                    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 