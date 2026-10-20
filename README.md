# 📚 AI Study Planner Agent

An Agentic AI system that transforms user learning goals into structured, day-wise study plans. Built using Python, Gemini LLM API, Streamlit, and Fetch.ai uAgents.

## Features
- **Goal Validation Tool:** Ensures realistic time allocations and descriptive study goals.
- **LLM-Powered Task Generation:** Dynamically breaks down study topics into daily actionable modules using Google Gemini.
- **Multi-Interface Support:** CLI tool, interactive Streamlit Web UI, and autonomous uAgent network integration.
- **Agentic Protocol:** Autonomous agent communication via Fetch.ai `uagents` framework.

## Project Structure
```text
AI-study-planner/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── planner.py       # Agent tools and LLM workflow
├── main.py          # Interactive CLI interface
├── app.py           # Streamlit Web UI
├── agent.py         # Fetch.ai uAgent node
└── user_agent.py    # Test agent client communication