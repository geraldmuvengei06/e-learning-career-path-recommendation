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
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SkillExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")
        # Load pre-defined skill taxonomies
        self.skill_taxonomy = self._load_skill_taxonomy()
        
    def _load_skill_taxonomy(self) -> Dict:
        """Load comprehensive skill taxonomy from JSON file."""
        with open('skill_taxonomy.json', 'r') as f:
            return json.load(f)
    
    def extract_from_resume(self, file_path: str) -> List[str]:
        """Extract skills from resume file (PDF or DOCX)."""
        text = self._extract_text_from_file(file_path)
        return self._extract_skills_from_text(text)
    
    def extract_from_linkedin(self, profile_data: Dict) -> List[str]:
        """Extract skills from LinkedIn profile data."""
        # Combine relevant sections of LinkedIn profile
        text = " ".join([
            profile_data.get('summary', ''),
            " ".join(profile_data.get('experiences', [])),
            " ".join(profile_data.get('skills', []))
        ])
        return self._extract_skills_from_text(text)
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from PDF or DOCX file."""
        if file_path.endswith('.pdf'):
            return self._extract_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self._extract_from_docx(file_path)
        raise ValueError("Unsupported file format")
    
    def _extract_from_pdf(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return " ".join(page.extract_text() for page in reader.pages)
    
    def _extract_from_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return " ".join(paragraph.text for paragraph in doc.paragraphs)
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using NLP and skill taxonomy."""
        doc = self.nlp(text)
        skills = set()
        
        # Extract skills using pattern matching and taxonomy
        for token in doc:
            # Check against skill taxonomy
            for category, category_skills in self.skill_taxonomy.items():
                if token.text.lower() in category_skills:
                    skills.add(token.text)
            
            # Extract technical terms and frameworks
            if token.ent_type_ in ['PRODUCT', 'ORG'] or \
               token.text.lower() in self.skill_taxonomy['technical']:
                skills.add(token.text)
        
        return list(skills)

class CareerAnalyzer:
    def __init__(self):
        self.openai_client = openai
        self._load_job_requirements()
    
    def _load_job_requirements(self):
        """Load job requirements for different roles."""
        with open('job_requirements.json', 'r') as f:
            self.job_requirements = json.load(f)
    
    async def analyze_skill_gaps(
        self, 
        career_goal: str, 
        current_skills: List[str]
    ) -> Dict:
        """Analyze skill gaps based on career goal and current skills."""
        # Get required skills for career goal using GPT
        required_skills = await self._get_required_skills(career_goal)
        
        # Convert skills to vectors for comparison
        vectorizer = TfidfVectorizer()
        all_skills = current_skills + required_skills
        skill_vectors = vectorizer.fit_transform(all_skills)
        
        # Calculate skill similarities
        similarities = cosine_similarity(skill_vectors)
        
        # Identify gaps and strengths
        gaps = self._identify_skill_gaps(
            required_skills, 
            current_skills, 
            similarities
        )
        
        return {
            'missing_skills': gaps['missing'],
            'partial_matches': gaps['partial'],
            'strength_areas': gaps['strengths'],
            'recommended_focus_areas': self._prioritize_gaps(gaps['missing'])
        }
    
    async def _get_required_skills(self, career_goal: str) -> List[str]:
        """Get required skills for a career goal using GPT."""
        prompt = f"""
        List the essential skills required for a {career_goal} position.
        Format the response as a JSON array of strings.
        Include both technical and soft skills.
        """
        
        response = await self.openai_client.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "You are a career counselor and industry expert."
            }, {
                "role": "user",
                "content": prompt
            }]
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _identify_skill_gaps(
        self, 
        required: List[str], 
        current: List[str], 
        similarities: np.ndarray
    ) -> Dict:
        """Identify skill gaps using similarity matrix."""
        gaps = {
            'missing': [],
            'partial': [],
            'strengths': []
        }
        
        for i, req_skill in enumerate(required):
            max_similarity = max(similarities[i, len(required):])
            if max_similarity < 0.3:
                gaps['missing'].append(req_skill)
            elif max_similarity < 0.7:
                gaps['partial'].append(req_skill)
            else:
                gaps['strengths'].append(req_skill)
        
        return gaps
    
    def _prioritize_gaps(self, missing_skills: List[str]) -> List[Dict]:
        """Prioritize skill gaps based on importance and learning difficulty."""
        prioritized = []
        for skill in missing_skills:
            importance = self._calculate_skill_importance(skill)
            difficulty = self._estimate_learning_difficulty(skill)
            prioritized.append({
                'skill': skill,
                'importance': importance,
                'difficulty': difficulty,
                'priority_score': importance / difficulty
            })
        
        return sorted(
            prioritized, 
            key=lambda x: x['priority_score'], 
            reverse=True
        )

class LearningRecommendationEngine:
    def __init__(self, api_keys: Dict[str, str]):
        """Initialize the recommendation engine with necessary components."""
        self.skill_extractor = SkillExtractor()
        self.career_analyzer = CareerAnalyzer()
        self.api_keys = api_keys
        self.db = self._initialize_firebase()
    
    async def process_user_input(
        self, 
        career_goal: str, 
        skill_source: Dict
    