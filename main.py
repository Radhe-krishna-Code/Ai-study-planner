"""
main.py - Execution script running the modular Agent workflow.
"""

from planner import run_agent_workflow

def display_plan(result: dict, goal: str):
    """Tool 5: Formats and displays the final agent output."""
    print("\n" + "=" * 50)
    print(f"YOUR TAILORED STUDY PLAN: {goal.upper()}")
    print(f"Total Dedicated Time: {result['total_hours']} hours")
    
    if result.get("warning"):
        print(f"⚠️  AGENT ADVISORY: {result['warning']}")
    print("=" * 50)

    for item in result["plan"]:
        sched = item["schedule"]
        print(f"\n📅 DAY {item['day']}")
        print(f"   Focus: {item['task']}")
        print(f"   Breakdown: {sched['theory_hrs']}h Theory | {sched['practice_hrs']}h Practice | {sched['review_hrs']}h Review")

    print("\n" + "=" * 50)


def main():
    print("=" * 50)
    print("      AI STUDY PLANNER AGENT - AGENTIC WORKFLOW      ")
    print("=" * 50)

    goal = input("\nWhat is your learning goal? (e.g., Python Functions): ").strip()
    
    try:
        days = int(input("How many days do you have? (e.g., 3): "))
        daily_hours = float(input("How many hours can you study each day? (e.g., 1.5): "))
    except ValueError:
        print("\n[Error] Days and daily hours must be valid numbers!")
        return

    # Trigger Agent Workflow
    print("\n[Agent] Evaluating inputs and invoking tools...")
    result = run_agent_workflow(goal, days, daily_hours)

    if not result["success"]:
        print(f"\n❌ [Agent Rejected Plan]: {result['error']}")
    else:
        display_plan(result, goal)


if __name__ == "__main__":
    main()