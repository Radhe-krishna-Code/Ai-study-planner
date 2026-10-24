import os
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv

# uAgents imports
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Registration import from the platform snippet
from uagents_core.utils.registration import (
    register_chat_agent,
    RegistrationRequestCredentials,
)

# Your existing planner logic
from planner import run_agent_workflow

load_dotenv()

# Setup Agent using Mailbox for secure cloud-to-local routing
AGENT_MAILBOX_KEY = os.getenv("AGENTVERSE_KEY") # We can use the same key for the mailbox
AGENT_SEED = os.getenv("AGENT_SEED_PHRASE", "ai_study_planner_secret_seed_phrase_12345")

study_agent = Agent(
    name="neuro_study_planner",
    seed=AGENT_SEED,
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
            ctx.logger.info(f"Received intent from {sender}: {item.text}")
            user_intent = item.text
            
            await ctx.send(sender, create_text_chat("⏳ Parsing intent and fetching live study resources..."))
            
            result = run_agent_workflow(user_text=user_intent)
            
            if not result["success"]:
                response_text = f"❌ **Error generating plan:** {result['error']}"
            else:
                response_text = f"🎯 **Your Personalized Study Plan: {result.get('goal', 'Study Plan').title()}**\n\n"
                response_text += f"**Total Expected Hours:** {result['total_hours']} hrs\n"
                if result.get("warning"):
                    response_text += f"⚠️ *Note: {result['warning']}*\n\n"
                
                for day in result["plan"]:
                    response_text += f"**Day {day['day']}**: {day['task']}\n"
                    response_text += f"   *Breakdown:* {day['schedule']['theory_hrs']}h Theory | {day['schedule']['practice_hrs']}h Practice\n"
                    response_text += f"   *Resource:* [{day['resource']['title']}]({day['resource']['url']})\n\n"
                
                response_text += "✅ **Action Complete!** External APIs have been queried for your resources."

            await ctx.send(sender, create_text_chat(response_text))

# --- THIS IS THE ADDED HANDLER TO FIX THE PROTOCOL VERIFICATION ERROR ---
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")

study_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    # 1. Register the agent with ASI:One so it can be discovered
    print("Registering agent with ASI:One...")
    register_chat_agent(
        name="AI Study Planner",
        endpoint="http://127.0.0.1:8000/submit",
        active=True,
        credentials=RegistrationRequestCredentials(
            agentverse_api_key=os.environ["AGENTVERSE_KEY"],
            agent_seed_phrase=os.environ["AGENT_SEED_PHRASE"],        
        ),
    )
    
    # 2. Run the agent locally
    study_agent.run()