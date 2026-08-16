import os
from typing import Dict

import langchain_google_genai
from google.genai.types import ListModelsConfig
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

def init_model() -> Dict:
    common_model = ChatOpenAI(
        model="gpt-5.1",
        temperature=0.3,
        timeout=300,
    )
    strong_model = ChatOpenAI(
        model="gpt-5.2",
        temperature=0.3,
        timeout=300,
    )
    fast_model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        timeout=300,
    )
    return {
        "Common": common_model,
        "Strong":  strong_model,
        "Fast": fast_model
    }

