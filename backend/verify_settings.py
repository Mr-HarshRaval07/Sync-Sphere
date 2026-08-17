import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from syncsphere.core.config.settings import settings

configs_to_check = {
    "GOOGLE_CLIENT_ID": "google_client_id",
    "GOOGLE_CLIENT_SECRET": "google_client_secret",
    "GOOGLE_REDIRECT_URI": "google_redirect_uri",
    "SLACK_CLIENT_ID": "slack_client_id",
    "SLACK_CLIENT_SECRET": "slack_client_secret",
    "SLACK_REDIRECT_URI": "slack_redirect_uri",
    "GITHUB_CLIENT_ID": "github_client_id",
    "GITHUB_CLIENT_SECRET": "github_client_secret",
    "GITHUB_REDIRECT_URI": "github_redirect_uri",
    "SYNCSPHERE_LLM_PROVIDER": "llm_provider",
    "SYNCSPHERE_LLM_MODEL": "llm_model",
    "SYNCSPHERE_LLM_API_KEY": "llm_api_key",
}

results = {}

for env_var, prop_name in configs_to_check.items():
    if hasattr(settings, prop_name):
        val = getattr(settings, prop_name)
        if hasattr(val, "get_secret_value"):
            val = val.get_secret_value()
        
        is_loaded = True
        is_none = val is None
        is_empty = str(val).strip() == "" if val is not None else False
    else:
        is_loaded = False
        is_none = True
        is_empty = False
        
    results[env_var] = {
        "loaded": is_loaded,
        "empty": is_empty,
        "None": is_none,
        "expected_configuration_name": prop_name
    }

with open("verify.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
