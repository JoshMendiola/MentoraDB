# CourseModels.py
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CourseStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseSection(BaseModel):
    id: str
    title: str
    content: str
    order: int
    reading_time_minutes: int


class CourseReview(BaseModel):
    id: str
    student_id: str
    rating: float
    comment: str
    created_at: datetime
    updated_at: datetime


class StudentProgress(BaseModel):
    student_id: str
    completed_sections: List[str]
    last_section_id: Optional[str]
    progress_percentage: float
    started_at: datetime
    last_accessed_at: datetime
    completed_at: Optional[datetime]


class Course(BaseModel):
    id: str
    title: str
    description: str
    difficulty_level: str
    estimated_hours: int
    sections: List[CourseSection]
    prerequisites: List[str]
    learning_objectives: List[str]
    category: str
    tags: List[str]
    status: str
    teacher_id: str
    teacher_name: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    # Enrollment and Progress
    enrolled_students: List[str] = []
    enrollment_count: int = 0
    completion_count: int = 0
    current_enrollment: int = 0

    # Ratings and Reviews
    reviews: List[CourseReview] = []
    average_rating: float = 0.0
    total_reviews: int = 0


class CourseCreationRequest(BaseModel):
    title: str
    description: str
    difficulty_level: str
    estimated_hours: int
    sections: List[dict]
    prerequisites: List[str]
    learning_objectives: List[str]
    category: str
    tags: List[str]
    status: str


class ErrorResponse(BaseModel):
    message: str
    errors: Optional[dict] = None


class CourseResponse(BaseModel):
    message: str
    course: Course

    class Config:
        arbitrary_types_allowed = True