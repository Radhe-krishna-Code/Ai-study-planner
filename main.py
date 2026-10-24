"""
main.py - Local testing script for the autonomous workflow.
"""
from planner import run_agent_workflow

def display_plan(result: dict):
    print("\n" + "=" * 60)
    print(f"🎯 AUTONOMOUS STUDY PLAN: {result['goal'].upper()}")
    print(f"Total Dedicated Time: {result['total_hours']} hours")
    
    if result.get("warning"):
        print(f"⚠️ AGENT ADVISORY: {result['warning']}")
    print("=" * 60)

    for item in result["plan"]:
        sched = item["schedule"]
        res = item["resource"]
        
        print(f"\n📅 DAY {item['day']}: {item['task']}")
        print(f"   ⏱️ {sched['theory_hrs']}h Theory | {sched['practice_hrs']}h Practice | {sched['review_hrs']}h Quiz")
        print(f"   🔗 Resource: {res['title']}")
        print(f"   🌐 Link: {res['url']}")

    print("\n" + "=" * 60)

def main():
    print("🤖 ASI:One Agent Simulator")
    
    # Simulating ASI:One natural language input
    user_input = input("\nSend message to agent (e.g., 'Help me learn Machine Learning in 4 days for 2 hours a day'):\n> ")
    
    print("\n[Agent] Parsing intent and executing tools...")
    result = run_agent_workflow(user_input)

    if not result["success"]:
        print(f"\n❌ [Agent Rejected Plan]: {result['error']}")
    else:
        display_plan(result)

if __name__ == "__main__":
    main()