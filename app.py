"""
app.py - Streamlit Web UI for the AI Study Planner Agent
"""

import streamlit as st
from planner import run_agent_workflow

st.set_page_config(page_title="AI Study Planner", page_icon="📚", layout="centered")

st.title("📚 AI Study Planner Agent")
st.caption("Powered by Gemini LLM & Agentic Tool Logic")

st.markdown("Enter your learning objective and available schedule to generate a personalized study plan.")

# Input Form
with st.form("planner_form"):
    goal = st.text_input("Learning Goal / Topic", value="Python Functions")
    
    col1, col2 = st.columns(2)
    with col1:
        days = st.number_input("Duration (Days)", min_value=1, max_value=30, value=3, step=1)
    with col2:
        daily_hours = st.number_input("Daily Study Time (Hours)", min_value=0.5, max_value=12.0, value=1.5, step=0.5)

    submit_button = st.form_submit_button("Generate Study Plan 🚀")

# Form Submission Processing
if submit_button:
    with st.spinner("Agent evaluating goal and generating AI schedule..."):
        result = run_agent_workflow(goal, int(days), float(daily_hours))

    if not result["success"]:
        st.error(f"❌ Plan Rejected: {result['error']}")
    else:
        if result.get("warning"):
            st.warning(f"⚠️ {result['warning']}")

        st.success("Plan Generated Successfully!")
        st.subheader(f"📋 Tailored Plan: {goal}")
        st.metric(label="Total Hours Required", value=f"{result['total_hours']} hrs")

        st.divider()

        for item in result["plan"]:
            with st.expander(f"📅 **Day {item['day']}**: {item['task']}", expanded=True):
                sched = item["schedule"]
                st.write(f"• **Theory:** {sched['theory_hrs']} hrs")
                st.write(f"• **Hands-on Practice:** {sched['practice_hrs']} hrs")
                st.write(f"• **Review & Quiz:** {sched['review_hrs']} hrs")