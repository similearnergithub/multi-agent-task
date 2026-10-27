
import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END

load_dotenv()

# 1. Configure the LLM
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError(
        "GOOGLE_API_KEY missing. Add it to your .env file."
    )

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    max_retries=5,
)


# 2. Python tool
@tool
def calculate_skill_match(
    required_skills: list[str],
    candidate_skills: list[str],
) -> dict:
    """Calculate matching and missing skills for a job."""
    required = {s.strip().lower() for s in required_skills if s.strip()}
    candidate = {s.strip().lower() for s in candidate_skills if s.strip()}

    matched = sorted(required & candidate)
    missing = sorted(required - candidate)

    score = round(len(matched) / len(required) * 100) if required else 0

    return {
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
    }


# 3. Shared state between agents
class AgentState(TypedDict, total=False):
    job_description: str
    candidate_skills: str
    job_analysis: str
    required_skills: list[str]
    match_report: dict
    recommendations: str
    final_report: str
    errors: list[str]



def ask_agent(role: str, prompt: str) -> str:
    response = llm.invoke([
        SystemMessage(content=role),
        HumanMessage(content=prompt),
    ])

    content = response.content

    # Gemini may return a list of content blocks instead of a string.
    if isinstance(content, list):
        text_parts = [
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ]
        return "\n".join(text_parts)

    if isinstance(content, str):
        return content

    raise ValueError("The model returned no readable text.")



# 4. Agent 1: Job Analyst


def job_analyst(state: AgentState) -> dict:
    print("\n[Agent 1] Analyzing job description...")

    try:
        analysis = ask_agent(
            "You are an expert job description analyst. "
            "Follow the output format exactly.",
            f"""
Analyze this job description:

{state['job_description']}

Identify:
1. Main responsibilities
2. Important keywords
3. Required technical skills
4. Preferred technical skills

Rules:
- Required skills are explicitly mandatory.
- Preferred skills are desirable or optional.
- Do not classify preferred skills as required.

End with exactly these two lines:
REQUIRED_SKILLS: Python, Machine Learning, NLP, SQL, Git
PREFERRED_SKILLS: TensorFlow, PyTorch, REST APIs

Use the actual job description to determine the skills.
These example lines show the required format only.
""",
        )

        print("\n[Agent 1] Raw response:")
        print(analysis)

        # Extract only the required skills.
        skills_line = ""

        for line in analysis.splitlines():
            normalized = line.strip().strip("*#` ")

            if normalized.lower().startswith("required_skills:"):
                skills_line = normalized.split(":", 1)[1].strip()
                break

        if not skills_line:
            raise ValueError(
                "Could not extract REQUIRED_SKILLS from Agent 1."
            )

        skills = [
            s.strip().strip("- *`")
            for s in skills_line.split(",")
            if s.strip()
        ]

        if not skills:
            raise ValueError("No required skills were extracted.")

        print("[Agent 1] Analysis completed.")
        print("[Agent 1] Required skills:", skills)

        return {
            "job_analysis": analysis,
            "required_skills": skills,
        }

    except Exception as exc:
        print(f"[Agent 1] Error: {exc}")
        return {
            "errors": [f"Job analyst failed: {exc}"]
        }


# 5. Agent 2: Application Strategist

def application_strategist(state: AgentState) -> dict:
    print("\n[Agent 2] Comparing skills and creating recommendations...")

    if not state.get("required_skills"):
        return {
            "errors": state.get("errors", [])
            + ["Agent 2 skipped: job analysis unavailable."]
        }

    try:
        candidate_skills = [
            s.strip()
            for s in state["candidate_skills"].split(",")
            if s.strip()
        ]

        # Match required skills using the deterministic tool.
        match_report = calculate_skill_match.invoke({
            "required_skills": state["required_skills"],
            "candidate_skills": candidate_skills,
        })

        # Extract preferred skills from Agent 1's analysis.
        preferred_line = next(
            (
                line.split(":", 1)[1].strip()
                for line in state["job_analysis"].splitlines()
                if line.strip().upper().startswith("PREFERRED_SKILLS:")
            ),
            "",
        )

        preferred_skills = [
            skill.strip()
            for skill in preferred_line.split(",")
            if skill.strip()
        ]

        # Calculate preferred-skill matches separately.
        preferred_report = calculate_skill_match.invoke({
            "required_skills": preferred_skills,
            "candidate_skills": candidate_skills,
        })

        recommendations = ask_agent(
            "You are a realistic career and resume strategist.",
            f"""
Agent 1's job analysis:
{state['job_analysis']}

Required skill matching results:
{match_report}

Preferred skill matching results:
{preferred_report}

Candidate skills:
{state['candidate_skills']}

Give practical resume improvements, learning priorities, and
interview preparation suggestions for a fresher.

Use the exact tool score. Do not invent candidate experience.
Clearly distinguish matched and missing required skills from
matched and missing preferred skills.
""",
        )

        print("[Agent 2] Recommendations completed.")

        return {
            "match_report": match_report,
            "recommendations": recommendations,
        }

    except Exception as exc:
        print(f"[Agent 2] Error: {exc}")
        return {
            "errors": state.get("errors", [])
            + [f"Strategist failed: {exc}"]
        }


# 6. Agent 3: Reviewer
def review_agent(state: AgentState) -> dict:
    print("\n[Agent 3] Reviewing agent outputs...")

    if not state.get("recommendations"):
        return {
            "final_report": (
                "The workflow could not complete.\n"
                + "\n".join(state.get("errors", []))
            )
        }

    try:
        final_report = ask_agent(
            "You are a strict reviewer. Verify consistency and "
            "never invent facts.",
            f"""
Combine these outputs into a useful final report.

JOB ANALYSIS:
{state.get('job_analysis', 'Unavailable')}

SKILL MATCH TOOL:
{state.get('match_report', {})}

STRATEGIST RECOMMENDATIONS:
{state['recommendations']}

Use these headings:
1. Job Summary
2. Skill Match Score
3. Matched Skills
4. Missing Skills
5. Resume Improvements
6. Learning Priorities
7. Interview Preparation

Preserve the exact score and skills from the tool.
""",
        )

        errors = state.get("errors", [])
        if errors:
            final_report += "\n\nWarnings:\n" + "\n".join(errors)

        print("[Agent 3] Final report generated.")
        return {"final_report": final_report}

    except Exception as exc:
        print(f"[Agent 3] Error: {exc}")
        return {
            "final_report": (
                "Review failed. Showing earlier recommendations:\n\n"
                + state["recommendations"]
                + f"\n\nReview error: {exc}"
            )
        }


# 7. Build the LangGraph workflow
builder = StateGraph(AgentState)

builder.add_node("job_analyst", job_analyst)
builder.add_node("application_strategist", application_strategist)
builder.add_node("review_agent", review_agent)

builder.add_edge(START, "job_analyst")
def after_job_analyst(state: AgentState) -> str:
    if state.get("job_analysis") and state.get("required_skills"):
        return "application_strategist"
    return "review_agent"


builder.add_conditional_edges(
    "job_analyst",
    after_job_analyst,
    {
        "application_strategist": "application_strategist",
        "review_agent": "review_agent",
    },
)

builder.add_edge("application_strategist", "review_agent")
builder.add_edge("review_agent", END)

graph = builder.compile()


# 8. Run the application
def main():
    print("=" * 50)
    print("MULTI-AGENT JOB APPLICATION ASSISTANT")
    print("=" * 50)

    job_description = input("\nPaste the job description:\n").strip()
    candidate_skills = input(
        "\nEnter candidate skills, separated by commas:\n"
    ).strip()

    if not job_description or not candidate_skills:
        print("Both inputs are required.")
        return

    try:
        result = graph.invoke({
            "job_description": job_description,
            "candidate_skills": candidate_skills,
            "errors": [],
        })

        print("\n" + "=" * 50)
        print("FINAL REPORT")
        print("=" * 50)
        print(result.get("final_report", "No report generated."))

    except Exception as exc:
        print(f"\nWorkflow error: {exc}")
        print("Check your API key, internet connection and model access.")


if __name__ == "__main__":
    main()
