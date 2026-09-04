"""Single route registry for the persistent application entrypoint."""
import streamlit as st

NAV_ITEMS = [
    {"file": "app.py", "path": "views/home.py", "icon": "\U0001F3E0", "label": "Home", "group": "Overview"},
    {"file": "0_Guided_Analysis.py", "path": "pages/0_Guided_Analysis.py", "icon": "\U0001F9ED", "label": "Analysis Workbench", "group": "Analyze"},
    {"file": "1_Getting_Started.py", "path": "pages/1_Getting_Started.py", "icon": "\U0001F680", "label": "Getting Started", "group": "Overview"},
    {"file": "2_Upload_and_Analyze.py", "path": "pages/2_Upload_and_Analyze.py", "icon": "\U0001F4C1", "label": "Upload & Analyze", "group": "Prepare"},
    {"file": "3_Data_Cleaning.py", "path": "pages/3_Data_Cleaning.py", "icon": "\U0001F9F9", "label": "Data Cleaning", "group": "Prepare"},
    {"file": "4_AI_Insights_Engine.py", "path": "pages/4_AI_Insights_Engine.py", "icon": "\U0001F916", "label": "AI Insights", "group": "Analyze"},
    {"file": "5_Advanced_Analytics.py", "path": "pages/5_Advanced_Analytics.py", "icon": "\U0001F527", "label": "Advanced Analytics", "group": "Analyze"},
    {"file": "6_Online_Data_Explorer.py", "path": "pages/6_Online_Data_Explorer.py", "icon": "\U0001F310", "label": "Online Explorer", "group": "Prepare"},
    {"file": "7_Report_Generator.py", "path": "pages/7_Report_Generator.py", "icon": "\U0001F4CB", "label": "Report Generator", "group": "Present"},
    {"file": "8_Chat_With_Data.py", "path": "pages/8_Chat_With_Data.py", "icon": "\U0001F4AC", "label": "Chat With Data", "group": "Analyze"},
    {"file": "9_Cloud_Workspace.py", "path": "pages/9_Cloud_Workspace.py", "icon": "\u2601\uFE0F", "label": "Cloud Workspace", "group": "Manage"},
    {"file": "10_Data_Profiling.py", "path": "pages/10_Data_Profiling.py", "icon": "\U0001F50D", "label": "Data Profiling", "group": "Prepare"},
    {"file": "11_Dashboard.py", "path": "pages/11_Dashboard.py", "icon": "\U0001F4CA", "label": "Dashboard", "group": "Present"},
    {"file": "12_Admin_Panel.py", "path": "pages/12_Admin_Panel.py", "icon": "\U0001F6E1\uFE0F", "label": "Admin Panel", "group": "Manage"},
    {"file": "13_Data_Join.py", "path": "pages/13_Data_Join.py", "icon": "\U0001F517", "label": "Data Join", "group": "Prepare"},
    {"file": "14_SQL_Query.py", "path": "pages/14_SQL_Query.py", "icon": "\U0001F4DD", "label": "SQL Query", "group": "Analyze"},
    {"file": "15_Data_Dictionary.py", "path": "pages/15_Data_Dictionary.py", "icon": "\U0001F4D6", "label": "Data Dictionary", "group": "Manage"},
]


def navigation_pages(user):
    groups = {name: [] for name in ("Overview", "Prepare", "Analyze", "Present", "Manage")}
    for item in NAV_ITEMS:
        if item["label"] == "Admin Panel" and (not user or user.get("role") != "admin"):
            continue
        home = item["label"] == "Home"
        url = "" if home else item["file"].split("_", 1)[1].removesuffix(".py")
        groups[item["group"]].append(st.Page(
            item["path"], title=item["label"], icon=item["icon"],
            default=home, url_path=url,
        ))
    return groups
