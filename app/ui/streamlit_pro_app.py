import os
import runpy

os.environ.setdefault("APP_ENV_FILE", "editions/pro/.env.pro")
os.environ.setdefault("APP_EDITION", "pro")
os.environ.setdefault("ADMIN_PAGE_TITLE", "Manage Apple Pro")
os.environ.setdefault("ADMIN_LOGIN_DEFAULT_USERNAME", "adminpro")
os.environ.setdefault("ADMIN_REQUIRED_ROLE", "admin_pro")
os.environ.setdefault("CHAT_LLM_PROVIDER", "openai")

runpy.run_module("app.ui.streamlit_app", run_name="__main__")
