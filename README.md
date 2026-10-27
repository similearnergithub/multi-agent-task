# Multi-Agent AI Job Application Assistant

## Overview

The Multi-Agent AI Job Application Assistant is a Python-based application that uses LangChain, LangGraph, and Google's Gemini model to analyze job descriptions, compare candidate skills, and generate personalized career recommendations.

The system uses three specialized agents that share information through a common state and work together to produce a final report.

## Features

- **Job Description Analyst:** Extracts responsibilities, important keywords, required skills, and preferred skills from a job description.
- **Application Strategist:** Compares candidate skills against job requirements using a deterministic Python tool and generates practical recommendations.
- **Review Agent:** Combines the outputs from the previous agents into a final report.
- **Skill Matching Tool:** Calculates the required-skill match percentage and identifies matched and missing skills.
- **Shared State:** Passes information between agents using LangGraph state.
- **Error Handling:** Captures agent failures and provides error messages when processing cannot continue normally.

## Tech Stack

- Python
- LangChain
- LangGraph
- Google Gemini API
- Python dotenv
- Pydantic

## System Architecture

The application follows a sequential multi-agent workflow:

1. The user enters a job description and candidate skills.
2. Agent 1 analyzes the job description and extracts required and preferred skills.
3. Agent 2 uses the skill-matching tool to calculate the match score and generates career recommendations.
4. Agent 3 reviews the available results and produces the final report.

**Workflow:**

`User Input → Job Analyst → Application Strategist → Review Agent → Final Report`

The agents communicate through a shared state managed by LangGraph.

## Project Structure

```text
task 1/
├── main.py
├── README.md
├── requirements.txt
├── .env
├── .gitignore
└── .venv/
```

- `main.py`: Contains the agents, skill-matching tool, shared state, and LangGraph workflow.
- `README.md`: Project documentation and setup instructions.
- `requirements.txt`: Python dependency list.
- `.env`: Stores the Google API key locally.
- `.gitignore`: Excludes sensitive files and generated files from version control.
- `.venv/`: Contains the project's Python virtual environment.

## Setup and Installation

### 1. Clone or open the project

Open the project folder in Visual Studio Code and open a PowerShell terminal.

### 2. Create a virtual environment

```powershell
py -3.14 -m venv .venv
```

### 3. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Configure the API key

Create a `.env` file in the project root and add your Google AI API key:

```text
GOOGLE_API_KEY=your_actual_api_key_here
```

Replace the placeholder with your own API key. Never commit your real API key to GitHub.

### 6. Run the application

```powershell
python main.py
```

Enter a job description and a comma-separated list of candidate skills when prompted.

## Application Output

The screenshot below shows the successful execution of the
three-agent workflow and the generated final report.

![Final Report](<output pic/Screenshot 2026-10-27 175920.png>)


## Skill Matching Logic

The skill-matching tool compares the candidate's skills with the required skills extracted from the job description.

The required-skill match percentage is calculated as:

`Match Score = (Matched Required Skills / Total Required Skills) × 100`

For example, if a job requires five skills and the candidate matches three, the required-skill match score is 60%.

Preferred skills are evaluated separately so that optional skills do not affect the required-skill match score.

## Error Handling

The application includes exception handling for agent execution and records errors in the shared state.

If job analysis fails or required skills are unavailable, the application strategist can skip processing and record an appropriate error. The review agent can then use the available state to produce a final response where possible.

## Limitations

- The quality of the analysis depends on the job description and the model's response.
- Skill matching uses the tool's defined matching logic; related skills or alternative names may not always be recognized as equivalent.
- Recommendations are AI-generated and should be reviewed before being used in a real job application.
- A valid Google API key and access to the configured Gemini model are required.

## Future Improvements

- Add resume upload and parsing.
- Support semantic skill matching and skill synonyms.
- Generate tailored resume bullet points and cover letters.
- Export the final report as PDF.
- Add automated tests for the skill-matching tool and agent workflow.

## Security

API keys and local environment files must not be committed to version control. The `.env` file should be excluded through `.gitignore`.

## Author

Developed as a multi-agent AI application demonstrating shared state, tool usage, workflow orchestration, and error handling.
