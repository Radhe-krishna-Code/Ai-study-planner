"""
agent.py - Fetch.ai uAgent implementation of the AI Study Planner Agent.
"""

from uagents import Agent, Context, Model
from planner import run_agent_workflow

class StudyRequest(Model):
    goal: str
    days: int
    daily_hours: float

class StudyResponse(Model):
    success: bool
    error: str = ""
    warning: str = ""
    total_hours: float = 0.0
    plan: list = []

# Added network="local" to suppress Almanac blockchain warnings
study_agent = Agent(
    name="study_planner_agent",
    seed="ai_study_planner_secret_seed_phrase_12345",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
    network="local"
)

@study_agent.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info(f"Agent online! Address: {study_agent.address}")

@study_agent.on_message(model=StudyRequest)
async def handle_request(ctx: Context, sender: str, msg: StudyRequest):
    ctx.logger.info(f"Received request from {sender} for goal: '{msg.goal}'")

    result = run_agent_workflow(msg.goal, msg.days, msg.daily_hours)

    if not result["success"]:
        response = StudyResponse(success=False, error=result["error"])
    else:
        response = StudyResponse(
            success=True,
            warning=result.get("warning", "") or "",
            total_hours=result["total_hours"],
            plan=result["plan"]
        )

    ctx.logger.info("Sending calculated plan back to sender...")
    await ctx.send(sender, response)

if __name__ == "__main__":
    study_agent.run()