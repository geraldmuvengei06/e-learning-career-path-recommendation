import spacy
import textract
import nltk
from typing import List, Dict, Set, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from fuzzywuzzy import fuzz
import json
import asyncio
import aiohttp
from datetime import datetime
from collections import defaultdict

class SkillTaxonomy:
    def __init__(self):
        self.career_paths = {
            "data_scientist": {
                "technical": {
                    "programming": ["python", "r", "sql", "scala", "julia"],
                    "machine_learning": ["scikit-learn", "tensorflow", "pytorch", "keras", "xgboost"],
                    "big_data": ["spark", "hadoop", "hive", "kafka"],
                    "databases": ["postgresql", "mongodb", "cassandra", "redis"]
                },
                "tools": {
                    "visualization": ["tableau", "power bi", "matplotlib", "seaborn", "plotly"],
                    "development": ["jupyter", "git", "docker", "aws", "azure"],
                    "analytics": ["sas", "spss", "excel", "rapidminer"]
                },
                "concepts": {
                    "statistics": ["hypothesis testing", "regression", "probability", "bayesian"],
                    "machine_learning": ["supervised learning", "unsupervised learning", "deep learning", "nlp"],
                    "math": ["linear algebra", "calculus", "optimization"]
                },
                "soft_skills": ["problem solving", "communication", "teamwork", "presentation"]
            },
            "software_engineer": {
                "technical": {
                    "frontend": ["javascript", "typescript", "react", "vue", "angular"],
                    "backend": ["python", "java", "nodejs", "go", "rust"],
                    "databases": ["mysql", "postgresql", "mongodb", "redis"],
                    "cloud": ["aws", "azure", "gcp", "kubernetes"]
                },
                "tools": {
                    "development": ["git", "docker", "jenkins", "jira"],
                    "testing": ["jest", "pytest", "selenium", "cypress"],
                    "monitoring": ["prometheus", "grafana", "datadog"]
                },
                "concepts": {
                    "architecture": ["microservices", "api design", "system design"],
                    "practices": ["agile", "tdd", "ci/cd", "devops"],
                    "security": ["oauth", "jwt", "encryption", "security best practices"]
                },
                "soft_skills": ["problem solving", "teamwork", "communication", "leadership"]
            },
            "devops_engineer": {
                "technical": {
                    "infrastructure": ["terraform", "ansible", "puppet", "chef"],
                    "containerization": ["docker", "kubernetes", "openshift"],
                    "cloud_platforms": ["aws", "azure", "gcp"],
                    "scripting": ["python", "bash", "powershell"]
                },
                "tools": {
                    "ci_cd": ["jenkins", "gitlab ci", "github actions", "travis ci"],
                    "monitoring": ["prometheus", "grafana", "elk stack", "datadog"],
                    "security": ["vault", "snyk", "sonarqube"]
                },
                "concepts": {
                    "practices": ["infrastructure as code", "gitops", "site reliability"],
                    "architecture": ["microservices", "containerization", "serverless"],
                    "security": ["devsecops", "zero trust", "compliance"]
                },
                "soft_skills": ["problem solving", "communication", "incident management"]
            }
            # Add more career paths as needed
        }

class DocumentProcessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")
        self.skill_patterns = self._load_skill_patterns()
        
    def _load_skill_patterns(self) -> Dict:
        """Load skill extraction patterns."""
        return {
            "prefixes": [
                "proficient in", "experience with", "knowledge of",
                "skilled in", "expertise in", "certified in",
                "worked with", "familiar with", "background in"
            ],
            "sections": [
                "technical skills", "skills", "expertise",
                "technologies", "competencies", "qualifications"
            ]
        }
        
    async def process_document(self, file_content: bytes, file_type: str) -> str:
        """Enhanced document processing with better text extraction."""
        try:
            if file_type == "pdf":
                text = await self._process_pdf(file_content)
            elif file_type in ["doc", "docx"]:
                text = await self._process_word(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
            # Clean and structure the extracted text
            return await self._clean_and_structure_text(text)
        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")
            
    async def _clean_and_structure_text(self, text: str) -> str:
        """Clean and structure extracted text."""
        # Remove special characters and normalize whitespace
        text = ' '.join(text.split())
        
        # Split into sections based on common resume headings
        sections = self._split_into_sections(text)
        
        # Process each section
        processed_sections = {}
        for section_name, section_text in sections.items():
            processed_sections[section_name] = await self._process_section(section_text)
            
        return processed_sections

class SkillMatcher:
    def __init__(self, taxonomy: SkillTaxonomy):
        self.taxonomy = taxonomy
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 3))
        self.threshold = 0.7
        
    async def match_skills(self, extracted_skills: List[str], career_path: str) -> Dict:
        """Match extracted skills against taxonomy using advanced matching."""
        career_skills = self.taxonomy.career_paths.get(career_path, {})
        matched_skills = defaultdict(dict)
        
        for category, subcategories in career_skills.items():
            if isinstance(subcategories, dict):
                for subcategory, skills in subcategories.items():
                    matches = await self._find_matches(extracted_skills, skills)
                    if matches:
                        matched_skills[category][subcategory] = matches
            else:
                matches = await self._find_matches(extracted_skills, subcategories)
                if matches:
                    matched_skills[category] = matches
                    
        return dict(matched_skills)
        
    async def _find_matches(self, extracted_skills: List[str], taxonomy_skills: List[str]) -> List[Dict]:
        """Find matches using multiple matching techniques."""
        matches = []
        
        # Vectorize skills
        all_skills = extracted_skills + taxonomy_skills
        tfidf_matrix = self.vectorizer.fit_transform(all_skills)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Find matches using multiple techniques
        for i, skill in enumerate(extracted_skills):
            best_matches = []
            
            # TF-IDF similarity
            similarities = similarity_matrix[i, len(extracted_skills):]
            
            # Fuzzy string matching
            fuzzy_scores = [fuzz.ratio(skill.lower(), tax_skill.lower()) / 100 
                          for tax_skill in taxonomy_skills]
            
            # Combine scores
            combined_scores = [0.7 * sim + 0.3 * fuzz 
                             for sim, fuzz in zip(similarities, fuzzy_scores)]
            
            # Get best matches
            for j, score in enumerate(combined_scores):
                if score > self.threshold:
                    best_matches.append({
                        "extracted": skill,
                        "matched": taxonomy_skills[j],
                        "confidence": float(score)
                    })
                    
            matches.extend(sorted(best_matches, key=lambda x: x["confidence"], reverse=True))
            
        return matches

class CourseRecommender:
    def __init__(self):
        self.course_providers = ["coursera", "udemy", "edx"]
        self.weights = {
            "skill_relevance": 0.4,
            "course_rating": 0.2,
            "completion_rate": 0.15,
            "recency": 0.15,
            "price": 0.1
        }
        
    async def get_recommendations(
        self,
        skill_gaps: Dict,
        career_path: str,
        preferences: Dict
    ) -> List[Dict]:
        """Get course recommendations with sophisticated ranking."""
        all_courses = []
        
        # Fetch courses from different providers
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_provider_courses(session, provider, skill_gaps)
                for provider in self.course_providers
            ]
            provider_courses = await asyncio.gather(*tasks)
            all_courses = [course for courses in provider_courses for course in courses]
            
        # Rank courses
        ranked_courses = await self._rank_courses(all_courses, skill_gaps, preferences)
        
        # Group by skill gap
        recommendations = self._group_recommendations(ranked_courses, skill_gaps)
        
        return recommendations
        
    async def _rank_courses(
        self,
        courses: List[Dict],
        skill_gaps: Dict,
        preferences: Dict
    ) -> List[Dict]:
        """Rank courses using multiple criteria."""
        ranked_courses = []
        
        for course in courses:
            # Calculate individual scores
            skill_score = self._calculate_skill_relevance(course, skill_gaps)
            rating_score = self._normalize_rating(course["rating"])
            completion_score = self._calculate_completion_score(course)
            recency_score = self._calculate_recency_score(course["published_date"])
            price_score = self._normalize_price(course["price"])
            
            # Calculate weighted total score
            total_score = (
                self.weights["skill_relevance"] * skill_score +
                self.weights["course_rating"] * rating_score +
                self.weights["completion_rate"] * completion_score +
                self.weights["recency"] * recency_score +
                self.weights["price"] * price_score
            )
            
            ranked_courses.append({
                **course,
                "relevance_score": total_score
            })
            
        return sorted(ranked_courses, key=lambda x: x["relevance_score"], reverse=True)
        
    def _group_recommendations(
        self,
        ranked_courses: List[Dict],
        skill_gaps: Dict
    ) -> Dict:
        """Group recommendations by skill gap category."""
        grouped_recommendations = defaultdict(list)
        
        for category, gaps in skill_gaps.items():
            relevant_courses = [
                course for course in ranked_courses
                if any(gap.lower() in course["skills_covered"].lower() for gap in gaps)
            ]
            grouped_recommendations[category] = relevant_courses[:5]  # Top 5 per category
            
        return dict(grouped_recommendations)

# Initialize the main components
class EnhancedLearningRecommendationEngine:
    def __init__(self, api_keys: Dict[str, str]):
        self.taxonomy = SkillTaxonomy()
        self.document_processor = DocumentProcessor()
        self.skill_matcher = SkillMatcher(self.taxonomy)
        self.course_recommender = CourseRecommender()
        
    async def process_and_recommend(
        self,
        career_goal: str,
        document: Dict,
        preferences: Dict
    ) -> Dict:
        """Process document and generate recommendations."""
        # Extract text from document
        processed_text = await self.document_processor.process_document(
            document["content"],
            document["type"]
        )
        
        # Match skills against taxonomy
        matched_skills = await self.skill_matcher.match_skills(
            processed_text["skills"],
            career_goal
        )
        
        # Identify skill gaps
        skill_gaps = self._identify_skill_gaps(matched_skills, career_goal)
        
        # Generate course recommendations
        recommendations = await self.course_recommender.get_recommendations(
            skill_gaps,
            career_goal,
            preferences
        )
        
        return {
            "matched_skills": matched_skills,
            "skill_gaps": skill_gaps,
            "recommendations": recommendations
        }
