import os
import warnings
import logging
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
#from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
import fitz  # PyMuPDF

# ✅ Load API keys safely from .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")

# ✅ Define OpenAI LLM
openai_llm = ChatOpenAI(model_name="gpt-4o")

# ✅ CV Reader Agent
cv_reader_agent = Agent(
    role="CV Reader",
    goal="Extract key details from the CV such as roles, skills, and experience.",
    backstory="A highly skilled AI that can read and analyze resumes.",
    verbose=True,
    llm=openai_llm  # ✅ Corrected model usage
)

# ✅ Google Job Search Agent
google_search_tool = SerperDevTool()
job_finder_agent = Agent(
    role="Job Finder",
    goal="Find relevant job openings in India based on the CV details. Make sure openings found align with work experience duration, dominant role in the CV and key industries worked in",
    backstory="A professional recruiter skilled in finding job listings.",
    tools=[google_search_tool],
    verbose=True,
    llm=openai_llm  # ✅ Corrected model usage
)

# ✅ Function to Read CV (PDF)
def read_pdf(file_path):
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

# Read CV file
cv_text = read_pdf("myPMCV.pdf")  # Ensure this file is in the same directory
print("\n📄 CV Extracted Text Preview:\n", cv_text[:1000])  # Show first 1000 characters

# ✅ Define CrewAI Tasks
extract_cv_task = Task(
    description=f"Extract total product management work experience, key product roles, dominant skills, key industries worked in, and major experience areas from the following CV:\n\n{cv_text}. Do not assume anyting of your own",
    expected_output="A structured list of roles, total work experience, key skills, industries, and dominant experience.",
    agent=cv_reader_agent
)

#Find jobs from entire google
job_search_task = Task(
    description="Search google for one month old job openings in India matching the dominant work experience and associated skills extracted from the CV. Extract only senior roles (VP, Director, Lead etc.). Location should be Delhi-NCR, Bangalore, Pune, Hyderabad only. Do not assume anyting of your own",
    expected_output="A list of at least 5 relevant job openings with links, location, work experience duration required, salary offered (if mentioned) and key skills asked.",
    tools=[google_search_tool],
    agent=job_finder_agent
)

# ✅ Define Crew
# ✅ CrewAI Setup
job_search_crew = Crew(
    agents=[cv_reader_agent, job_finder_agent],
    tasks=[extract_cv_task, job_search_task],
    process=Process.sequential
)


# ✅ Test CrewAI to ensure it's working correctly
#print("\n🔍 Running CrewAI Test...")
#test_results = job_search_crew.test(n_iterations=3)
#print("\n📝 Test Results:\n", test_results)

# ✅ Train CrewAI to improve results
#print("\n🎯 Running CrewAI Training...")
#training_results = job_search_crew.train(n_iterations=3, filename="crew_training_data.json")
#print("\n📊 Training Results:\n", training_results)

# ✅ Run Crew
result = job_search_crew.kickoff()

# ✅ Format Output as Markdown
markdown_output = f"""
# 📌 **Job Search Results**  
### 🔍 Extracted CV Details:  
{result}  
"""

# ✅ Save to a .txt File
with open("job_search_results.txt", "w", encoding="utf-8") as file:
    file.write(markdown_output)

print("✅ Results saved to 'job_search_results.txt'")
