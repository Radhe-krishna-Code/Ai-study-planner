"""
user_agent.py - Client agent that sends a study request to study_planner_agent.
"""

from uagents import Agent, Bureau, Context, Model
from agent import study_agent, StudyRequest, StudyResponse

# Added network="local" to suppress Almanac blockchain warnings
user_agent = Agent(
    name="user_agent", 
    seed="user_agent_secret_seed_phrase_999",
    network="local"
)

TARGET_ADDRESS = study_agent.address

@user_agent.on_event("startup")
async def send_plan_request(ctx: Context):
    ctx.logger.info("User Agent online. Sending request to Study Planner Agent...")
    request = StudyRequest(goal="Machine Learning Basics", days=3, daily_hours=2.0)
    await ctx.send(TARGET_ADDRESS, request)

@user_agent.on_message(model=StudyResponse)
async def handle_plan_response(ctx: Context, sender: str, msg: StudyResponse):
    ctx.logger.info(f"Received plan from Study Planner Agent ({sender}):")
    if not msg.success:
        ctx.logger.error(f"Plan Error: {msg.error}")
    else:
        ctx.logger.info(f"Total Hours: {msg.total_hours}")
        for item in msg.plan:
            ctx.logger.info(f"Day {item['day']}: {item['task']}")

bureau = Bureau(port=8000, endpoint="http://127.0.0.1:8000/submit")
bureau.add(study_agent)
bureau.add(user_agent)

if __name__ == "__main__":
    bureau.run()