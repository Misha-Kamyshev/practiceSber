import os
from typing import Optional, List, Any

from dotenv import load_dotenv
from langchain_core.callbacks import CallbackManagerForLLMRun

from langchain_gigachat.chat_models import GigaChat
from langchain_core.language_models import LLM
from gigachat import GigaChat
from pydantic import PrivateAttr

from aiogram import Bot, Dispatcher

load_dotenv()

AUTHORIZATION_KEY = os.getenv("AUTHORIZATION_KEY")
DATA_SOURCE = os.getenv("DATA_SOURCE")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

giga = GigaChat(
    credentials=AUTHORIZATION_KEY,
    verify_ssl_certs=False,
    model="GigaChat"
)


class GigaChatLLM(LLM):
    _client: GigaChat = PrivateAttr()

    def __init__(self, credentials: str, model: str = "GigaChat", verify_ssl: bool = False):
        super().__init__()
        self._client = GigaChat(credentials=credentials, model=model, verify_ssl_certs=verify_ssl)

    @property
    def _llm_type(self) -> str:
        return "giga-chat"

    def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any
    ) -> str:
        response = self._client.chat({
            "messages": [{"role": "user", "content": prompt}]
        })
        return response.choices[0].message.content

    @property
    def _identifying_params(self) -> dict:
        return {
            "model_name": "GigaChat"
        }
