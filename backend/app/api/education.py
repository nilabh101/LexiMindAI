"""
Education API — Phase 1.
Serves curriculum data (courses, subjects, chapters, concepts) from
static configuration. In Phase 2 this will be backed by a database
with user-contributed content.

All routes are under /api/education/...
"""
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/education", tags=["education"])

# ─── Static curriculum data (mirrors frontend data/curriculum.ts) ─────────────
# In Phase 2 this will be loaded from the DB / admin panel.

COURSES = [
    # School
    {"id": "class-6",  "name": "Class 6",  "educationLevel": "school", "yearRange": [6]},
    {"id": "class-7",  "name": "Class 7",  "educationLevel": "school", "yearRange": [7]},
    {"id": "class-8",  "name": "Class 8",  "educationLevel": "school", "yearRange": [8]},
    {"id": "class-9",  "name": "Class 9",  "educationLevel": "school", "yearRange": [9]},
    {"id": "class-10", "name": "Class 10", "educationLevel": "school", "yearRange": [10]},
    {"id": "class-11", "name": "Class 11", "educationLevel": "school", "yearRange": [11],
     "streams": [
         {"id": "science",  "name": "Science",  "subjects": ["physics-11","chemistry-11","maths-11","biology-11"]},
         {"id": "commerce", "name": "Commerce", "subjects": ["accounts-11","economics-11","business-11","maths-11"]},
         {"id": "arts",     "name": "Arts",     "subjects": ["history-11","geography-11","political-science-11","economics-11"]},
     ]},
    {"id": "class-12", "name": "Class 12", "educationLevel": "school", "yearRange": [12],
     "streams": [
         {"id": "science",  "name": "Science",  "subjects": ["physics-12","chemistry-12","maths-12","biology-12"]},
         {"id": "commerce", "name": "Commerce", "subjects": ["accounts-12","economics-12","business-12","maths-12"]},
         {"id": "arts",     "name": "Arts",     "subjects": ["history-12","geography-12","political-science-12","economics-12"]},
     ]},
    # College
    {"id": "btech-cse",   "name": "B.Tech CSE",          "shortName": "CSE",   "educationLevel": "college", "yearRange": [1,2,3,4]},
    {"id": "btech-ece",   "name": "B.Tech ECE",          "shortName": "ECE",   "educationLevel": "college", "yearRange": [1,2,3,4]},
    {"id": "btech-mech",  "name": "B.Tech Mechanical",   "shortName": "Mech",  "educationLevel": "college", "yearRange": [1,2,3,4]},
    {"id": "btech-civil", "name": "B.Tech Civil",        "shortName": "Civil", "educationLevel": "college", "yearRange": [1,2,3,4]},
    {"id": "bca",         "name": "BCA",                 "shortName": "BCA",   "educationLevel": "college", "yearRange": [1,2,3]},
    {"id": "bsc-cs",      "name": "B.Sc Computer Science","shortName": "B.Sc CS","educationLevel": "college","yearRange": [1,2,3]},
    {"id": "bsc-maths",   "name": "B.Sc Mathematics",    "shortName": "B.Sc Maths","educationLevel": "college","yearRange": [1,2,3]},
    {"id": "bcom",        "name": "B.Com",               "shortName": "B.Com", "educationLevel": "college", "yearRange": [1,2,3]},
    {"id": "bba",         "name": "BBA",                 "shortName": "BBA",   "educationLevel": "college", "yearRange": [1,2,3]},
    {"id": "ba",          "name": "B.A",                 "shortName": "B.A",   "educationLevel": "college", "yearRange": [1,2,3]},
]

SUBJECTS = [
    {
        "id": "em1-btech", "name": "Engineering Mathematics I", "shortName": "EM-I",
        "courseId": "btech-cse", "semester": 1, "year": 1,
        "color": "indigo", "icon": "📐",
        "description": "Differential calculus, matrices, and complex numbers.",
        "chapterIds": ["dc-em1","matrices-em1","complex-em1"], "totalChapters": 3,
    },
    {
        "id": "programming-btech", "name": "Programming in C", "shortName": "C Prog",
        "courseId": "btech-cse", "semester": 1, "year": 1,
        "color": "blue", "icon": "💻",
        "description": "Introduction to programming using C language.",
        "chapterIds": ["intro-c","control-flow-c","functions-c","arrays-c","pointers-c"], "totalChapters": 5,
    },
    {
        "id": "physics-btech", "name": "Engineering Physics", "shortName": "Phy",
        "courseId": "btech-cse", "semester": 1, "year": 1,
        "color": "emerald", "icon": "⚛️",
        "description": "Optics, wave mechanics, and quantum physics.",
        "chapterIds": ["optics-phy","waves-phy","quantum-phy"], "totalChapters": 3,
    },
    {
        "id": "maths-10", "name": "Mathematics", "shortName": "Maths",
        "courseId": "class-10", "year": 10,
        "color": "purple", "icon": "➗",
        "description": "Algebra, geometry, trigonometry, and statistics.",
        "chapterIds": ["real-numbers-10","polynomials-10","quadratic-10","trig-10","circles-10","stats-10"],
        "totalChapters": 6,
    },
    {
        "id": "science-10", "name": "Science", "shortName": "Sci",
        "courseId": "class-10", "year": 10,
        "color": "teal", "icon": "🔬",
        "description": "Physics, Chemistry, and Biology.",
        "chapterIds": ["chemical-reactions-10","electricity-10","heredity-10","light-10"], "totalChapters": 4,
    },
]

CHAPTERS = [
    {
        "id": "dc-em1", "name": "Differential Calculus", "subjectId": "em1-btech", "order": 1,
        "estimatedMinutes": 180,
        "conceptIds": ["limits-dc","derivatives-dc","partial-derivatives-dc","euler-theorem-dc","total-derivatives-dc"],
        "description": "Limits, derivatives, partial derivatives, and their applications.",
    },
    {
        "id": "matrices-em1", "name": "Matrices & Linear Algebra", "subjectId": "em1-btech", "order": 2,
        "estimatedMinutes": 150,
        "conceptIds": ["matrix-ops","determinants","eigen-values","cayley-hamilton"],
        "description": "Matrix operations, determinants, eigenvalues, and eigenvectors.",
    },
    {
        "id": "intro-c", "name": "Introduction to C", "subjectId": "programming-btech", "order": 1,
        "estimatedMinutes": 90,
        "conceptIds": ["c-basics","data-types-c","operators-c"],
        "description": "History, structure, compilation, variables, and data types.",
    },
    {
        "id": "control-flow-c", "name": "Control Flow", "subjectId": "programming-btech", "order": 2,
        "estimatedMinutes": 120,
        "conceptIds": ["if-else-c","loops-c","switch-c"],
        "description": "Decision making, loops, and branching statements.",
    },
    {
        "id": "quadratic-10", "name": "Quadratic Equations", "subjectId": "maths-10", "order": 3,
        "estimatedMinutes": 90,
        "conceptIds": ["quad-roots","discriminant","nature-of-roots","sum-product-roots"],
        "description": "Methods of solving quadratic equations and their applications.",
    },
    {
        "id": "trig-10", "name": "Trigonometry", "subjectId": "maths-10", "order": 4,
        "estimatedMinutes": 120,
        "conceptIds": ["trig-ratios","trig-identities","trig-heights-distances"],
        "description": "Trigonometric ratios, identities, and applications.",
    },
]

CONCEPTS = [
    {
        "id": "limits-dc", "name": "Limits and Continuity",
        "chapterId": "dc-em1", "subjectId": "em1-btech",
        "difficulty": "beginner", "estimatedMinutes": 30, "prerequisites": [],
        "description": "Understanding limits, indeterminate forms, L'Hôpital's rule, and continuity.",
        "keyPoints": ["Limit of a function as x→a","Left/right-hand limits","L'Hôpital's rule","Continuity"],
    },
    {
        "id": "derivatives-dc", "name": "Derivatives",
        "chapterId": "dc-em1", "subjectId": "em1-btech",
        "difficulty": "beginner", "estimatedMinutes": 30, "prerequisites": ["limits-dc"],
        "description": "Differentiation of single-variable functions and the standard rules.",
        "keyPoints": ["Derivative as a limit","Product and quotient rules","Chain rule","Higher-order derivatives"],
    },
    {
        "id": "partial-derivatives-dc", "name": "Partial Derivatives",
        "chapterId": "dc-em1", "subjectId": "em1-btech",
        "difficulty": "intermediate", "estimatedMinutes": 40, "prerequisites": ["derivatives-dc"],
        "description": "Partial differentiation of functions with multiple variables.",
        "keyPoints": ["∂f/∂x and ∂f/∂y","Higher-order partial derivatives","Mixed partials","Clairaut's theorem"],
        "formulaSummary": "∂f/∂x = lim(h→0) [f(x+h,y) - f(x,y)] / h",
    },
    {
        "id": "euler-theorem-dc", "name": "Euler's Theorem",
        "chapterId": "dc-em1", "subjectId": "em1-btech",
        "difficulty": "intermediate", "estimatedMinutes": 35, "prerequisites": ["partial-derivatives-dc"],
        "description": "Euler's theorem on homogeneous functions and its corollary.",
        "keyPoints": ["Homogeneous function definition","Euler's theorem formula","Deductions and corollary","Applications"],
        "formulaSummary": "x·(∂f/∂x) + y·(∂f/∂y) = n·f",
    },
    {
        "id": "total-derivatives-dc", "name": "Total Derivatives",
        "chapterId": "dc-em1", "subjectId": "em1-btech",
        "difficulty": "intermediate", "estimatedMinutes": 40, "prerequisites": ["euler-theorem-dc"],
        "description": "Total differential, chain rule for partial derivatives.",
        "keyPoints": ["Total differential df","Chain rule for composite functions","Implicit differentiation","Applications to error analysis"],
        "formulaSummary": "df = (∂f/∂x)dx + (∂f/∂y)dy",
    },
    {
        "id": "c-basics", "name": "C Basics",
        "chapterId": "intro-c", "subjectId": "programming-btech",
        "difficulty": "beginner", "estimatedMinutes": 25, "prerequisites": [],
        "description": "Structure of a C program, compilation, and basic I/O.",
        "keyPoints": ["#include, main(), printf, scanf","Compilation steps","Variables and identifiers"],
    },
    {
        "id": "loops-c", "name": "Loops in C",
        "chapterId": "control-flow-c", "subjectId": "programming-btech",
        "difficulty": "beginner", "estimatedMinutes": 30, "prerequisites": ["c-basics"],
        "description": "for, while, do-while loops and loop control statements.",
        "keyPoints": ["for loop syntax","while and do-while","break and continue","Nested loops"],
    },
    {
        "id": "discriminant", "name": "Discriminant",
        "chapterId": "quadratic-10", "subjectId": "maths-10",
        "difficulty": "intermediate", "estimatedMinutes": 20, "prerequisites": ["quad-roots"],
        "description": "Using the discriminant to determine the nature of roots.",
        "keyPoints": ["D = b²−4ac","D>0: two real distinct roots","D=0: two equal roots","D<0: no real roots"],
        "formulaSummary": "D = b² - 4ac",
    },
]

# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/courses")
def list_courses(education_level: Optional[str] = None):
    if education_level:
        return [c for c in COURSES if c["educationLevel"] == education_level]
    return COURSES

@router.get("/courses/{course_id}")
def get_course(course_id: str):
    course = next((c for c in COURSES if c["id"] == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    return course

@router.get("/subjects")
def list_subjects(course_id: Optional[str] = None, year: Optional[int] = None):
    subs = SUBJECTS
    if course_id:
        subs = [s for s in subs if s["courseId"] == course_id]
    if year:
        subs = [s for s in subs if s.get("year") == year]
    return subs

@router.get("/subjects/{subject_id}")
def get_subject(subject_id: str):
    subject = next((s for s in SUBJECTS if s["id"] == subject_id), None)
    if not subject:
        raise HTTPException(status_code=404, detail=f"Subject '{subject_id}' not found")
    return subject

@router.get("/chapters")
def list_chapters(subject_id: Optional[str] = None):
    chs = CHAPTERS
    if subject_id:
        chs = [c for c in chs if c["subjectId"] == subject_id]
    return sorted(chs, key=lambda x: x.get("order", 0))

@router.get("/chapters/{chapter_id}")
def get_chapter(chapter_id: str):
    chapter = next((c for c in CHAPTERS if c["id"] == chapter_id), None)
    if not chapter:
        raise HTTPException(status_code=404, detail=f"Chapter '{chapter_id}' not found")
    return chapter

@router.get("/concepts")
def list_concepts(chapter_id: Optional[str] = None, subject_id: Optional[str] = None):
    cons = CONCEPTS
    if chapter_id:
        cons = [c for c in cons if c["chapterId"] == chapter_id]
    if subject_id:
        cons = [c for c in cons if c["subjectId"] == subject_id]
    return cons

@router.get("/concepts/{concept_id}")
def get_concept(concept_id: str):
    concept = next((c for c in CONCEPTS if c["id"] == concept_id), None)
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{concept_id}' not found")
    return concept

@router.get("/health")
def education_health():
    return {
        "status": "ok",
        "courses": len(COURSES),
        "subjects": len(SUBJECTS),
        "chapters": len(CHAPTERS),
        "concepts": len(CONCEPTS),
    }
