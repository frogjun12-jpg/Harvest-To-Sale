import os
import runpy

os.environ.setdefault("APP_ENV_FILE", "editions/pro/.env.pro")
os.environ.setdefault("SHOP_EDITION", "pro")
os.environ.setdefault("SHOP_PAGE_TITLE", "Harvest to sale")
os.environ.setdefault("SHOP_LOGIN_DEFAULT_USERNAME", "customerpro")
os.environ.setdefault("SHOP_REQUIRED_ROLE", "customer_pro")

runpy.run_module("app.ui.shop_app", run_name="__main__")
