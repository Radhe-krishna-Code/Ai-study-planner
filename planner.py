"""
planner.py - Tool set and LLM integration for the Study Planner Agent.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Find .env explicitly in the project folder
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


def validate_goal(goal: str) -> tuple[bool, str]:
    """Tool 1: Validates that the goal string is meaningful."""
    cleaned = goal.strip()
    if not cleaned:
        return False, "Goal cannot be empty."
    if len(cleaned) < 3:
        return False, "Goal is too short. Please provide a clear topic."
    if cleaned.isdigit():
        return False, "Goal should be a descriptive topic, not just numbers."
    return True, ""


def check_plan(days: int, daily_hours: float) -> tuple[bool, str, str]:
    """Tool 2: Evaluates constraints and provides feedback/warnings."""
    total_hours = days * daily_hours

    if days <= 0 or daily_hours <= 0:
        return False, "ERROR", "Days and daily hours must be positive numbers."
    if daily_hours > 10:
        return False, "ERROR", "Studying over 10 hours daily leads to severe burnout!"
    
    if total_hours < 2:
        return True, "WARNING", f"Total time ({total_hours:.1f} hrs) is very low."
    if total_hours > 60:
        return True, "WARNING", f"Total time ({total_hours:.1f} hrs) is high."
        
    return True, "OK", "Plan parameters are well balanced."


def calculate_daily_schedule(daily_hours: float) -> dict:
    """Tool 3: Calculates detailed time distribution for a study session."""
    return {
        "theory_hrs": round(daily_hours * 0.4, 1),
        "practice_hrs": round(daily_hours * 0.5, 1),
        "review_hrs": round(daily_hours * 0.1, 1)
    }


def create_llm_study_tasks(goal: str, days: int) -> list[str]:
    """
    Tool 4 (LLM-Powered): Connects to Google Gemini API to generate structured daily topics.
    """
    # 1. First tries to read key from .env file
    api_key = os.getenv("GEMINI_API_KEY")

    # 2. If .env fails, put your real API key string directly between the quotes below
    if not api_key or api_key == "GEMINI_API_KEY":
        api_key = "GEMINI_API_KEY"

    if not api_key or "PASTE_YOUR_REAL_API_KEY_HERE" in api_key:
        print("⚠️ [Notice] API key not configured. Using fallback generator.")
        return [f"Day {d}: Fundamentals of {goal} (Part {d}/{days})" for d in range(1, days + 1)]

    try:
        client = genai.Client(api_key="GEMINI_API_KEY"
)
        
        prompt = f"""
        Break down the learning goal '{goal}' into exactly {days} daily study topic titles.
        Return ONLY a JSON array of strings with no markdown or formatting outside JSON.
        Example format: ["Day 1: Intro to topic", "Day 2: Advanced topic"]
        """

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )

        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        tasks = json.loads(cleaned_text)
        
        if isinstance(tasks, list) and len(tasks) == days:
            return tasks
        else:
            raise ValueError("Returned list length mismatch.")

    except Exception as e:
        print(f"⚠️ [API Warning] LLM call failed ({e}). Using fallback tasks.")
        return [f"Day {d}: Module on {goal} (Part {d}/{days})" for d in range(1, days + 1)]


def run_agent_workflow(goal: str, days: int, daily_hours: float) -> dict:
    """
    Agent Workflow: Invokes validation tools, LLM task generator, and schedule engine.
    """
    is_goal_valid, goal_err = validate_goal(goal)
    if not is_goal_valid:
        return {"success": False, "error": goal_err}

    is_feasible, warning_level, check_msg = check_plan(days, daily_hours)
    if not is_feasible:
        return {"success": False, "error": check_msg}

    tasks = create_llm_study_tasks(goal, days)
    time_split = calculate_daily_schedule(daily_hours)

    daily_plan = []
    for day_num, task_title in enumerate(tasks, start=1):
        daily_plan.append({
            "day": day_num,
            "task": task_title,
            "schedule": time_split
        })

    return {
        "success": True,
        "warning": check_msg if warning_level == "WARNING" else None,
        "total_hours": round(days * daily_hours, 1),
        "plan": daily_plan
    }