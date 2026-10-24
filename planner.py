"""
planner.py - Upgraded for Fetch.ai ASI:One Challenge (Intent-to-Action)
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Ensure your API key is properly loaded
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY") 
client = genai.Client(api_key=API_KEY)


def extract_user_intent(user_text: str) -> dict:
    """
    Tool 1 (Intent Extractor): ASI:One sends natural language. 
    This tool uses the LLM to extract the structured parameters required by the agent.
    """
    prompt = f"""
    Extract the study goal, number of days, and daily hours from this request: "{user_text}"
    If days are missing, default to 3. If hours are missing, default to 1.5.
    Return ONLY valid JSON in this exact format: {{"goal": "string", "days": int, "daily_hours": float}}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception as e:
        print(f"⚠️ Intent extraction failed: {e}")
        # Fallback if LLM fails
        return {"goal": user_text[:30], "days": 3, "daily_hours": 1.5}


def fetch_real_resource(topic: str) -> dict:
    """
    Tool 2 (External API Action): Fulfills the hackathon requirement to use external APIs.
    Fetches a real, live Wikipedia summary and URL for the given topic.
    """
    # Clean topic for URL (take first two words to broaden search)
    query = "_".join(topic.split()[:2])
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title", "Resource"),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "summary": data.get("extract", "")[:100] + "..."
            }
    except Exception:
        pass
    
    return {"title": "Google Search", "url": f"https://www.google.com/search?q={topic.replace(' ', '+')}+tutorial", "summary": "Search for tutorials."}


def check_plan(days: int, daily_hours: float) -> tuple[bool, str, str]:
    """Tool 3: Evaluates constraints and provides agentic reasoning."""
    total_hours = days * daily_hours
    if days <= 0 or daily_hours <= 0:
        return False, "ERROR", "Days and daily hours must be positive numbers."
    if daily_hours > 10:
        return False, "ERROR", "Studying over 10 hours daily leads to severe burnout!"
    if total_hours < 2:
        return True, "WARNING", f"Total time ({total_hours:.1f} hrs) is very low."
    return True, "OK", "Plan parameters are well balanced."


def calculate_daily_schedule(daily_hours: float) -> dict:
    """Tool 4: Time allocation."""
    return {
        "theory_hrs": round(daily_hours * 0.4, 1),
        "practice_hrs": round(daily_hours * 0.5, 1),
        "review_hrs": round(daily_hours * 0.1, 1)
    }


def create_llm_study_tasks(goal: str, days: int) -> list[str]:
    """Tool 5: Breaks down the goal into daily topics."""
    prompt = f"""
    Break down the learning goal '{goal}' into exactly {days} daily study topic titles.
    Return ONLY a JSON array of strings. Example format: ["Day 1: Intro to topic", "Day 2: Advanced topic"]
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()
        tasks = json.loads(cleaned)
        if isinstance(tasks, list) and len(tasks) == days:
            return tasks
    except Exception as e:
        print(f"⚠️ Task generation failed: {e}")
    
    return [f"Module on {goal} (Part {d}/{days})" for d in range(1, days + 1)]


def run_agent_workflow(user_text: str) -> dict:
    """
    Orchestrator: Connects Intent -> Validation -> Task Gen -> Resource Fetching.
    """
    # 1. Parse natural language intent
    intent = extract_user_intent(user_text)
    goal = intent.get("goal", "General Study")
    days = intent.get("days", 3)
    daily_hours = intent.get("daily_hours", 1.5)

    if len(goal) < 3:
        return {"success": False, "error": "Goal is too short or unclear."}

    # 2. Validate constraints
    is_feasible, warning_level, check_msg = check_plan(days, daily_hours)
    if not is_feasible:
        return {"success": False, "error": check_msg}

    # 3. Generate tasks
    tasks = create_llm_study_tasks(goal, days)
    time_split = calculate_daily_schedule(daily_hours)

    # 4. Fetch real-world external resources (Action)
    daily_plan = []
    for day_num, task_title in enumerate(tasks, start=1):
        resource = fetch_real_resource(task_title)
        daily_plan.append({
            "day": day_num,
            "task": task_title,
            "schedule": time_split,
            "resource": resource  # Includes live links
        })

    return {
        "success": True,
        "goal": goal,
        "warning": check_msg if warning_level == "WARNING" else None,
        "total_hours": round(days * daily_hours, 1),
        "plan": daily_plan
    }