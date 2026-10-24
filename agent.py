import os
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.utils.registration import (
    register_chat_agent,
    RegistrationRequestCredentials,
)
from planner import run_agent_workflow

load_dotenv()

AGENT_MAILBOX_KEY = os.getenv("AGENTVERSE_KEY")
AGENT_SEED = os.getenv("AGENT_SEED_PHRASE", "ai_study_planner_secret_seed_phrase_12345")

study_agent = Agent(
    name="neuro_study_planner",
    seed=AGENT_SEED,
    port=8001,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai"
)

chat_proto = Protocol(spec=chat_protocol_spec)

def create_text_chat(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)],
    )

@study_agent.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info(f"Agent online! Address: {study_agent.address}")

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))
    
    for item in msg.content:
        if isinstance(item, TextContent):
            user_input = item.text.strip()
            
            # Fetch user's current conversation state from agent's memory
            user_state = ctx.storage.get(sender) or {"step": "ask_topic"}
            
            if user_state["step"] == "ask_topic":
                # Step 1: Greet and ask for the subject
                user_state["step"] = "ask_days"
                ctx.storage.set(sender, user_state)
                await ctx.send(sender, create_text_chat("👋 Hello! I am your Agentic AI Study Planner. What topic do you want to study? (e.g., Python, Machine Learning)"))
                
            elif user_state["step"] == "ask_days":
                # Step 2: Save topic, ask for days
                user_state["topic"] = user_input
                user_state["step"] = "ask_hours"
                ctx.storage.set(sender, user_state)
                await ctx.send(sender, create_text_chat(f"Great choice! You want to study **{user_input}**. How many days do you want to dedicate to this?"))
                
            elif user_state["step"] == "ask_hours":
                # Step 3: Save days, ask for hours
                user_state["days"] = user_input
                user_state["step"] = "generate_plan"
                ctx.storage.set(sender, user_state)
                await ctx.send(sender, create_text_chat(f"Got it, **{user_input} days**. And how many hours per day can you study?"))
                
            elif user_state["step"] == "generate_plan":
                # Step 4: Save hours, combine everything, and generate plan
                user_state["hours"] = user_input
                
                await ctx.send(sender, create_text_chat(f"⏳ Perfect! Generating your plan for {user_state['topic']} ({user_state['days']} days, {user_state['hours']} hrs/day). Fetching live links..."))
                
                # Combine into the prompt your planner.py expects
                combined_prompt = f"Topic: {user_state['topic']}, Duration: {user_state['days']} days, Time per day: {user_state['hours']} hours."
                
                result = run_agent_workflow(user_text=combined_prompt)
                
                if not result["success"]:
                    response_text = f"❌ **Error:** {result['error']}"
                else:
                    response_text = f"🎯 **Your AI Study Plan: {result.get('goal', 'Study Plan').title()}**\n\n"
                    for day in result["plan"]:
                        response_text += f"**Day {day['day']}**: {day['task']}\n"
                        response_text += f"   *Resource:* [{day['resource']['title']}]({day['resource']['url']})\n\n"
                    response_text += "✅ **Done!** Type 'Hi' if you want to create a completely new plan."
                
                await ctx.send(sender, create_text_chat(response_text))
                
                # Clear memory so user can start a new chat later
                ctx.storage.set(sender, {"step": "ask_topic"})

@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass # Kept clean to avoid terminal spam

study_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    register_chat_agent(
        name="AI Study Planner",
        endpoint="http://127.0.0.1:8001/submit",
        active=True,
        credentials=RegistrationRequestCredentials(
            agentverse_api_key=os.environ.get("AGENTVERSE_KEY"),
            agent_seed_phrase=os.environ.get("AGENT_SEED_PHRASE"),        
        ),
    )
    study_agent.run()