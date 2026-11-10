import os
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("api key kha hai bro")
client=Groq(api_key=my_api_key)
model="openai/gpt-oss-120b"
job_description="""
Job Title: Software Development Engineer (SDE)
Location: Bengaluru, India
Experience: 0–2 years
Employment Type: Full-time

Job Description:
We are looking for a motivated Software Development Engineer (SDE) to join our engineering team. The candidate will be responsible for designing, developing, testing, and maintaining scalable software applications.

Responsibilities:

Develop and maintain high-quality, scalable software applications.
Write clean, efficient, and maintainable code.
Work with cross-functional teams to understand requirements and deliver solutions.
Design and implement REST APIs and backend services.
Debug and troubleshoot software issues.
Write unit tests and participate in code reviews.
Work with databases and external APIs.
Follow software development best practices and version-control workflows.
Continuously learn and adopt new technologies.

Required Skills:

Strong programming knowledge in Python, Java, or C++.
Good understanding of Data Structures and Algorithms.
Knowledge of Object-Oriented Programming (OOP).
Familiarity with SQL and databases.
Understanding of REST APIs and backend development.
Knowledge of Git/GitHub.
Good problem-solving and analytical skills.

Preferred Skills:

Experience with FastAPI, Django, or Spring Boot.
Familiarity with cloud platforms such as AWS/Azure/GCP.
Basic knowledge of Docker and CI/CD.
Experience working on software development projects.

Education:
Bachelor's degree in Computer Science, Information Technology, Artificial Intelligence, or a related field.

What We Offer:

Opportunity to work on real-world software projects.
Mentorship from experienced engineers.
Learning and professional growth opportunities.
Collaborative and technology-driven work environment.
"""
class JobD(BaseModel):
    role: str
    required_skills: list[str]
    preferred_skills: list[str]
    minimum_experience: float | None
    education_requirements: list[str]
    responsibilities: list[str]

jobd_schema=JobD.model_json_schema()

system_prompt=f"""
You are expert HR assistant.
Your job is to analyze job descriptions and extract structured information from them.
Return only valid json matching schema:
{jobd_schema}
IMPORTANT:
Do not Return the schema itself.
Do not return fields like "properties","title" or "type".
Fill the schema with actual information extracted from the job description.
If minimum experience is not mentioned,return null.
If information for the list is missing, return an empty list.
DO NOT INVENT INFORMATION
"""
user_prompt=f"""
Analyze the following job description:
{job_description}
"""
message_system={
    "role": "system",
    "content": system_prompt
}
message_user={
    "role":"user",
    "content": user_prompt
}
response_format={
    "type": "json_object"
}
messages=[message_system,message_user]
response=client.chat.completions.create(model=model,messages=messages,response_format=response_format)

answer=response.choices[0].message.content
raw_json=answer

import json
job_data=json.loads(raw_json)

job=JobD(**job_data)
print(job.minimum_experience)
print(job.education_requirements)
#part 2 of the project(resume's schema )
class MatchResult(BaseModel):
    score: float
    details: dict
class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: list[str]=[]

class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience_years: float | None = None 

    skills: list[str]=[]
    experiences: list[Experience]=[]
    education: list[str]=[]
    projects: list[str]=[]
    certifications: list[str]=[]
#used Resume class to make resume_schema 
resume_schema=Resume.model_json_schema()

def final_score(job,resume):
    match_schema=MatchResult.model_json_schema()
    prompt=f"""
    You are an HR recruiter.
    compare the candidate's resume with the job description.
    JOB DESCRIPTION:
    {job.model_dump_json(indent=2)}
    CANDIDATE'S RESUME:
    {resume.model_dump_json(indent=2)}
    Return JSON matching this schema:
    {match_schema}
     
    Give me:
    1. Candidate name 
    2. Matching Skills
    3. Missing Skills
    4. Whether experience requirement is met
    5. Overall match percentage from 0 to 100
    6. A short final verdict 
    Keep the response concise and easy to read.
    """
    message={
        "role":"user",
        "content":prompt
    }
    messages=[message]
    response_format={
        "type":"json_object"
    }
    response=client.chat.completions.create(model=model,messages=messages,response_format=response_format)
    data=json.loads(response.choices[0].message.content)
    return MatchResult(**data)
def parse_resume(resume_text):
    system_prompt=f"""
    You are an expert resume parser.
    Extract information from the resume based on its meaning,
    not only based on exact section heading.
    differrnt resume may use diffrent heading.

    For Example:
    -Experience
    -Professional experience
    -Work History 
    -Employement 
    -Internships
    These may all contaion relevent experience.

    skills may also appear in the skill section, work experience,
    internships or projects.

    Return only valid JSON matching this schema:
    {resume_schema}
    
    Important rules:
    1. Do not invent information.
    2. If a value is not available return null.
    3. If a list has no information return an empty list.
    4. Include internships inside experience.
    5. Extract skills across the entire resume.
    """
    user_prompt=f"""
    parse the following resume:
    {resume_text}
    
    """
    message_system={
        "role":"system",
        "content":system_prompt
    }
    message_user={
        "role":"user",
        "content":user_prompt
    }
    messages=[message_system,message_user]
    response_format={
        "type":"json_object"
    }
    response=client.chat.completions.create(model=model,messages=messages,response_format=response_format)
    raw_output=response.choices[0].message.content
    data=json.loads(raw_output)
    resume=Resume(**data)
    return resume


# RESUME PARSE 
from pypdf import PdfReader
from docx import Document

def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            test += page_text + "\n"
    return text

def read_docx(file_path): #doc has paragraphs and tables, we dont have page 
    Document= Document(file_path)
    text= ""
    for paragraph in Document.paragraphs:
        if paragraph.text.strip():
            text += paragraph.text + "\n"
    for table in Document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip:
                    text += cell.text + "\n"
    return text


def read_resume(file_path):
    if file_path.suffix.lower == ".pdf":
        return read_pdf(file_path)
    elif file_path.suffix.lower == "docx":
        return read_docx(file_path)
    else:
        return None

resume_folder=Path("resumes")
all_results=[]
for file_path in resume_folder.iterdir():
    if file_path.suffix.lower() not in [".pdf","docx"]: #screenshot ya image bhjne pe discard kr diyaa
        continue
    print("\nprocessing:", file_path.name)
    resume_text= read_resume(file_path)
    parsed_resume= parse_resume(resume_text) #llm call 1
    time.sleep(5)
    result=final_score(job,parsed_resume) #llm call 2
    time.sleep(5)

    print("score:", result.score)
    all_results.append({
        "name": parsed_resume.name,
        "score": result.score,
        "details": result.details
    })
all_results.sort(
        key=lambda candidate: candidate["score"],
        reverse=True)

Top_2=all_results[:2]
worst_2=all_results[-2:]
print("TOP 2 CANDIDATES")
for candidate in Top_2:
    print(
        candidate["name"],
        "-",
        candidate["score"],
        "%"
    )
    print(candidate["details"])

print("lowest 2 candidate")
for candidate in worst_2:
    print(
        candidate["name"],
        "-",
        candidate["score"],
        "%"
    )
    print(candidate["details"])




