import os
from datetime import datetime
from uuid import uuid4
from uagents import Model, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, TextContent, chat_protocol_spec,
)

class PlanRequest(Model):
    sender_id: str
    topic: str
    days: str
    hours: str

class PlanResponse(Model):
    sender_id: str
    plan_text: str

chat_proto = Protocol(spec=chat_protocol_spec)

def create_text_chat(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)],
    )

@chat_proto.on_message(ChatMessage)
async def handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))
    
    for item in msg.content:
        if isinstance(item, TextContent):
            user_input = item.text.strip()
            user_state = ctx.storage.get(sender) or {"step": "ask_topic"}
            
            if user_state["step"] == "ask_topic":
                user_state["step"] = "ask_days"
                ctx.storage.set(sender, user_state)
                await ctx.send(sender, create_text_chat("👋 Hello! I am your Cloud-Hosted MAS Study Planner. What topic do you want to study?"))
                
            elif user_state["step"] == "ask_days":
                user_state["topic"] = user_input
                user_state["step"] = "ask_hours"
                ctx.storage.set(sender, user_state)
                await ctx.send(sender, create_text_chat(f"How many days for **{user_input}**?"))
                
            elif user_state["step"] == "ask_hours":
                user_state["days"] = user_input
                user_state["step"] = "generate_plan"
                ctx.storage.set(sender, user_state)
                await ctx.send(sender, create_text_chat(f"And how many hours per day?"))
                
            elif user_state["step"] == "generate_plan":
                user_state["hours"] = user_input
                await ctx.send(sender, create_text_chat("⏳ Sending data to Backend AI Planner... Please wait!"))
                
                planner_addr = os.environ.get("PLANNER_ADDRESS")
                req = PlanRequest(
                    sender_id=sender, 
                    topic=user_state["topic"], 
                    days=user_state["days"], 
                    hours=user_state["hours"]
                )
                await ctx.send(planner_addr, req)
                ctx.storage.set(sender, {"step": "ask_topic"})

@agent.on_message(model=PlanResponse)
async def handle_response(ctx: Context, sender: str, msg: PlanResponse):
    await ctx.send(msg.sender_id, create_text_chat(msg.plan_text))

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass

agent.include(chat_proto, publish_manifest=True)