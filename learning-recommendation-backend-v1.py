import spacy
from typing import List, Dict
from collections import defaultdict
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import openai

class LearningRecommendationEngine:
    def __init__(self, api_keys: Dict[str, str]):
        """Initialize the recommendation engine with necessary API keys."""
        self.nlp = spacy.load("en_core_web_lg")
        self.api_keys = api_keys
        self.db = self._initialize_firebase()
        
    def _initialize_firebase(self):
        """Initialize Firebase connection."""
        cred = credentials.Certificate("path/to/serviceAccount.json")
        firebase_admin.initialize_app(cred)
        return firestore.client()

    async def process_user_data(self, user_data: Dict) -> Dict:
        """Process user input and generate initial profile."""
        profile = {
            "user_id": self._generate_user_id(),
            "timestamp": datetime.now(),
            "career_goals": self._extract_career_goals(user_data["careerGoals"]),
            "current_skills": self._extract_skills(user_data["currentSkills"]),
            "learning_style": user_data["preferredLearningStyle"],
            "linkedin_data": await self._fetch_linkedin_data(user_data["linkedInUrl"])
        }
        
        return profile

    def _extract_career_goals(self, goals_text: str) -> List[str]:
        """Extract structured career goals from free text."""
        doc = self.nlp(goals_text)
        # Extract key phrases and career-related entities
        career_goals = []
        for chunk in doc.noun_chunks:
            if any(career_term in chunk.text.lower() for career_term in 
                  ["developer", "engineer", "manager", "analyst", "designer"]):
                career_goals.append(chunk.text)
        return career_goals

    def _extract_skills(self, skills_text: str) -> Dict[str, List[str]]:
        """Categorize skills into technical and soft skills."""
        doc = self.nlp(skills_text)
        skills = {
            "technical": [],
            "soft": []
        }
        
        # Define skill categories
        technical_indicators = ["programming", "software", "database", "framework"]
        soft_indicators = ["communication", "leadership", "teamwork", "management"]
        
        for token in doc:
            if any(tech in token.text.lower() for tech in technical_indicators):
                skills["technical"].append(token.text)
            elif any(soft in token.text.lower() for soft in soft_indicators):
                skills["soft"].append(token.text)
                
        return skills

    async def generate_recommendations(self, user_profile: Dict) -> Dict:
        """Generate course recommendations based on user profile."""
        recommendations = {
            "courses": await self._fetch_course_recommendations(user_profile),
            "learning_path": await self._generate_learning_path(user_profile),
            "skill_gaps": self._analyze_skill_gaps(user_profile)
        }
        
        # Store recommendations in Firebase
        self._store_recommendations(user_profile["user_id"], recommendations)
        
        return recommendations

    async def _fetch_course_recommendations(self, profile: Dict) -> List[Dict]:
        """Fetch relevant courses from Coursera and Udemy APIs."""
        courses = []
        
        # Fetch from Coursera
        coursera_courses = await self._fetch_coursera_courses(profile["career_goals"])
        courses.extend(coursera_courses)
        
        # Fetch from Udemy
        udemy_courses = await self._fetch_udemy_courses(profile["career_goals"])
        courses.extend(udemy_courses)
        
        # Sort and filter based on user's learning style
        return self._filter_courses_by_learning_style(
            courses, 
            profile["learning_style"]
        )

    async def _generate_learning_path(self, profile: Dict) -> List[Dict]:
        """Use GPT to generate a personalized learning path."""
        prompt = self._construct_learning_path_prompt(profile)
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "You are an expert career counselor and education planner."
            }, {
                "role": "user",
                "content": prompt
            }]
        )
        
        return self._parse_gpt_learning_path(response.choices[0].message.content)

    def _analyze_skill_gaps(self, profile: Dict) -> Dict:
        """Analyze gaps between current skills and career goal requirements."""
        required_skills = self._fetch_job_requirements(profile["career_goals"])
        current_skills = set(profile["current_skills"]["technical"] + 
                           profile["current_skills"]["soft"])
        
        return {
            "missing_skills": list(required_skills - current_skills),
            "strength_areas": list(current_skills & required_skills),
            "recommended_focus_areas": self._prioritize_skill_gaps(
                list(required_skills - current_skills)
            )
        }

    def _store_recommendations(self, user_id: str, recommendations: Dict):
        """Store recommendations in Firebase for future reference."""
        doc_ref = self.db.collection("recommendations").document(user_id)
        doc_ref.set({
            "timestamp": datetime.now(),
            "recommendations": recommendations,
            "status": "active"
        })

    def _filter_courses_by_learning_style(
        self, 
        courses: List[Dict], 
        learning_style: str
    ) -> List[Dict]:
        """Filter and rank courses based on user's learning style preference."""
        style_keywords = {
            "video": ["video", "lecture", "watch"],
            "interactive": ["project", "hands-on", "practice"],
            "reading": ["book", "article", "reading"]
        }
        
        # Score courses based on learning style match
        scored_courses = []
        for course in courses:
            score = self._calculate_learning_style_score(
                course, 
                learning_style, 
                style_keywords
            )
            scored_courses.append((score, course))
            
        # Sort by score and return top courses
        return [course for _, course in sorted(
            scored_courses, 
            key=lambda x: x[0], 
            reverse=True
        )]
