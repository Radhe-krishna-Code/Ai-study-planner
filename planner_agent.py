import os
import aiohttp
from uagents import Model, Context

class PlanRequest(Model):
    sender_id: str
    topic: str
    days: str
    hours: str

class PlanResponse(Model):
    sender_id: str
    plan_text: str

async def get_gemini_response(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers={"Content-Type": "application/json"}, json=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return "Error generating plan."

@agent.on_message(model=PlanRequest)
async def handle_request(ctx: Context, sender: str, msg: PlanRequest):
    ctx.logger.info(f"Received request for {msg.topic}")
    api_key = os.environ.get("GEMINI_API_KEY")
    
    prompt = f"Act as an AI study planner. Create a structured study plan for {msg.topic} over {msg.days} days, spending {msg.hours} hours a day. Include specific topics and resources. Make it clear and use Markdown."
    
    plan = await get_gemini_response(prompt, api_key)
    await ctx.send(sender, PlanResponse(sender_id=msg.sender_id, plan_text=plan))