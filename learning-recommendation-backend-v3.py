import spacy
from typing import List, Dict, Tuple
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import openai
import PyPDF2
import docx
import linkedin_api
from collections import defaultdict
import json
import asyncio
import aiohttp

class SkillExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")
        # Load pre-defined skill taxonomies
        self.skill_taxonomies = self._load_skill_taxonomies()
        
    def _load_skill_taxonomies(self) -> Dict:
        """Load skill taxonomies for different career paths."""
        # This would typically load from a database or file
        return {
            "data_scientist": {
                "technical": ["python", "r", "sql", "machine learning", "deep learning", "statistics"],
                "tools": ["pandas", "sklearn", "tensorflow", "jupyter", "tableau"],
                "concepts": ["regression", "classification", "clustering", "neural networks"],
                "soft_skills": ["problem solving", "communication", "data visualization"]
            },
            # Add more career paths...
        }
    
    async def extract_skills_from_resume(self, file_content: bytes, file_type: str) -> List[str]:
        """Extract skills from resume file."""
        text = ""
        if file_type == "pdf":
            reader = PyPDF2.PdfReader(file_content)
            text = " ".join([page.extract_text() for page in reader.pages])
        elif file_type in ["doc", "docx"]:
            doc = docx.Document(file_content)
            text = " ".join([paragraph.text for paragraph in doc.paragraphs])
            
        return await self._process_text_for_skills(text)
    
    async def extract_skills_from_linkedin(self, profile_url: str) -> List[str]:
        """Extract skills from LinkedIn profile."""
        # Initialize LinkedIn API client
        api = linkedin_api.Linkedin()
        profile_data = await api.get_profile(profile_url)
        
        # Extract skills from various profile sections
        skills = []
        skills.extend(profile_data.get('skills', []))
        skills.extend(self._extract_skills_from_experience(profile_data.get('experience', [])))
        return skills
    
    async def _process_text_for_skills(self, text: str) -> List[str]:
        """Process text to extract skills using NLP."""
        doc = self.nlp(text.lower())
        skills = set()
        
        # Extract skills using named entity recognition and pattern matching
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG", "TECH"]:
                skills.add(ent.text)
                
        # Use phrase matching for common skill patterns
        skill_patterns = [
            "proficient in", "experience with", "knowledge of",
            "skilled in", "expertise in", "certified in"
        ]
        
        for pattern in skill_patterns:
            if pattern in text.lower():
                # Get the text following the pattern
                index = text.lower().find(pattern) + len(pattern)
                relevant_text = text[index:index + 100]  # Look at next 100 chars
                skills.update(self._extract_skills_from_chunk(relevant_text))
                
        return list(skills)

class CareerAnalyzer:
    def __init__(self):
        self.openai_client = openai.Client()
        
    async def analyze_career_requirements(self, career_goal: str) -> Dict:
        """Analyze requirements for a specific career path."""
        prompt = f"""
        Analyze the key requirements for a {career_goal} role, including:
        1. Essential technical skills
        2. Required tools and technologies
        3. Important concepts and knowledge areas
        4. Relevant soft skills
        5. Common certification requirements
        Format the response as a structured JSON object.
        """
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.choices[0].message.content)

class SkillGapAnalyzer:
    def __init__(self, skill_extractor: SkillExtractor, career_analyzer: CareerAnalyzer):
        self.skill_extractor = skill_extractor
        self.career_analyzer = career_analyzer
        
    async def analyze_skill_gaps(
        self,
        career_goal: str,
        current_skills: List[str],
        career_requirements: Dict
    ) -> Dict:
        """Analyze gaps between current skills and career requirements."""
        # Normalize skills for comparison
        normalized_current = set(skill.lower() for skill in current_skills)
        
        gaps = {
            "missing_technical": [],
            "missing_tools": [],
            "missing_concepts": [],
            "missing_soft_skills": [],
            "recommended_certifications": []
        }
        
        # Compare against requirements
        for category in career_requirements:
            required = set(skill.lower() for skill in career_requirements[category])
            missing = required - normalized_current
            gaps[f"missing_{category}"] = list(missing)
            
        return gaps

class LearningRecommendationEngine:
    def __init__(self, api_keys: Dict[str, str]):
        self.skill_extractor = SkillExtractor()
        self.career_analyzer = CareerAnalyzer()
        self.gap_analyzer = SkillGapAnalyzer(self.skill_extractor, self.career_analyzer)
        self.api_keys = api_keys
        self.db = self._initialize_firebase()
        
    async def process_user_input(
        self,
        career_goal: str,
        skill_source: str,
        input_data: Dict
    ) -> Dict:
        """Process user input and generate comprehensive analysis."""
        # Extract skills based on source
        if skill_source == "resume":
            current_skills = await self.skill_extractor.extract_skills_from_resume(
                input_data["file_content"],
                input_data["file_type"]
            )
        elif skill_source == "linkedin":
            current_skills = await self.skill_extractor.extract_skills_from_linkedin(
                input_data["profile_url"]
            )
        else:  # manual input
            current_skills = await self.skill_extractor._process_text_for_skills(
                input_data["skills_text"]
            )
            
        # Analyze career requirements
        career_requirements = await self.career_analyzer.analyze_career_requirements(
            career_goal
        )
        
        # Analyze skill gaps
        skill_gaps = await self.gap_analyzer.analyze_skill_gaps(
            career_goal,
            current_skills,
            career_requirements
        )
        
        # Generate learning recommendations
        recommendations = await self._generate_learning_recommendations(
            career_goal,
            skill_gaps
        )
        
        return {
            "current_skills": current_skills,
            "career_requirements": career_requirements,
            "skill_gaps": skill_gaps,
            "recommendations": recommendations
        }
        
    async def _generate_learning_recommendations(
        self,
        career_goal: str,
        skill_gaps: Dict
    ) -> Dict:
        """Generate personalized learning recommendations based on skill gaps."""
        recommendations = {
            "courses": [],
            "learning_path": [],
            "resources": []
        }
        
        # Fetch course recommendations
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_coursera_recommendations(session, skill_gaps),
                self._fetch_udemy_recommendations(session, skill_gaps)
            ]
            course_results = await asyncio.gather(*tasks)
            
        recommendations["courses"] = self._merge_and_rank_courses(course_results)
        
        # Generate learning path
        recommendations["learning_path"] = await self._generate_learning_path(
            career_goal,
            skill_gaps
        )
        
        return recommendations
