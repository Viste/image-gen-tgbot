import json
import logging
from calendar import monthrange
from datetime import date

from openai import AsyncOpenAI
import requests
import tiktoken

from tools.utils import config

logger = logging.getLogger(__name__)


class UserHistoryManager:
    _instance = None
    user_dialogs: dict[int: list] = {}

    def __init__(self):
        self.content = """ТУТ НАДО ОПИСАТЬ ЛИЧНОСТЬ БОТА ЖЕЛАТЕЛЬНО В json формате(или любой формать ключ-значение), на удивление OPENAI такое воспринимает лучше простого текстовое описание"""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserHistoryManager, cls).__new__(cls)
        return cls._instance

    async def add_to_history(self, user_id, role, content):
        if user_id not in self.user_dialogs:
            await self.reset_history(user_id)
        self.user_dialogs[user_id].append({"role": role, "content": content})

    async def reset_history(self, user_id, content=''):
        if content == '':
            content = self.content
        self.user_dialogs[user_id] = [{"role": "system", "content": content}]

    async def trim_history(self, user_id, max_history_size):
        if user_id in self.user_dialogs:
            self.user_dialogs[user_id] = self.user_dialogs[user_id][-max_history_size:]


class OpenAI:
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-4-1106-preview"
        self.client = AsyncOpenAI(api_key=config.api_key, base_url='http://176.222.52.92:9000/v1')
        self.history = UserHistoryManager()
        self.max_retries = 5
        self.max_tokens = 16096
        self.config_tokens = 1024
        self.max_history_size = 10
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.args = {
            "temperature": 0.1, "max_tokens": 1024, "top_p": 1, "frequency_penalty": 0, "presence_penalty": 0.8, "stop": None
            }

    async def add_to_history(self, user_id, role, content):
        await self.history.add_to_history(user_id, role, content)

    async def reset_history(self, user_id, content=''):
        await self.history.reset_history(user_id, content)

    async def get_resp(self, query: str, chat_id: int) -> tuple[str, int]:
        response = await self._query_gpt(chat_id, query)
        answer = ''

        logger.info('Response: %s, Answer: %s', response, answer)
        if response.choices and len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice.message.content.strip()
                if index == 0:
                    await self.add_to_history(chat_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        elif response.choices and len(response.choices) >= 0:
            answer = response.choices[0].message.content.strip()
            await self.add_to_history(chat_id, role="assistant", content=answer)
        else:
            answer = response.choices[0].message.content.strip()
            await self.add_to_history(chat_id, role="assistant", content=answer)

        total_tokens = response.usage.total_tokens if response.usage else 0
        if response.usage and self.show_tokens:
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage.total_tokens)}" \
                      f" ({str(response.usage.prompt_tokens)} prompt," \
                      f" {str(response.usage.completion_tokens)} completion)"

        return answer, total_tokens

    async def _query_gpt(self, user_id, query):
        while self.retries < self.max_retries:
            try:
                if user_id not in self.history.user_dialogs:
                    await self.reset_history(user_id)

                await self.add_to_history(user_id, role="user", content=query)

                token_count = self._count_tokens(self.history.user_dialogs[user_id])
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(self.history.user_dialogs[user_id]) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self._summarise(self.history.user_dialogs[user_id][:-1])
                        logging.info(f'Summary: {summary}')
                        await self.reset_history(user_id)
                        await self.add_to_history(user_id, role="assistant", content=summary)
                        await self.add_to_history(user_id, role="user", content=query)
                        logging.info("Dialog From summary: %s", self.history.user_dialogs[user_id])
                    except Exception as e:
                        logging.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        await self.history.trim_history(user_id, self.max_history_size)
                        logging.info("Dialog From summary exception: %s", self.history.user_dialogs[user_id])

                return await self.client.chat.completions.create(model=self.model, messages=self.history.user_dialogs[user_id], **self.args)

            except self.client.error.RateLimitError as e:
                self.retries += 1
                logging.info("Dialog From Ratelim: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except self.client.error.InvalidRequestError as er:
                self.retries += 1
                logging.info("Dialog From bad req: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 1
                logging.info("Dialog From custom exception: %s", self.history.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err

    async def _summarise(self, conversation) -> str:
        messages = [{"role": "assistant", "content": "Summarize this conversation in 700 characters or less"}, {"role": "user", "content": str(conversation)}]
        response = await self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.1)
        return response.choices[0].message.content

    def _count_tokens(self, messages) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-3.5-turbo-16k")

        tokens_per_message = 3
        tokens_per_name = -1

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens

    @staticmethod
    def get_money():
        headers = {
            "Authorization": f"Bearer {config.api_key}"
            }
        today = date.today()
        first_day = date(today.year, today.month, 1)
        _, last_day_of_month = monthrange(today.year, today.month)
        last_day = date(today.year, today.month, last_day_of_month)
        params = {
            "start_date": first_day, "end_date": last_day
            }
        response = requests.get("https://api.openai.com/dashboard/billing/usage", headers=headers, params=params)
        billing_data = json.loads(response.text)
        usage_month = billing_data["total_usage"] / 100
        return usage_month

    async def send_dalle(self, data):
        while self.retries < self.max_retries:
            try:
                result = await self.client.images.generate(model="dall-e-3", prompt=data + "4k resolution", n=1, size="1024x1024")
                return result.url

            except await self.client.error.RateLimitError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: Превышены лимиты ⚠️\n{str(e)}') from e

            except await self.client.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: кривой запрос ⚠️\n{str(e)}') from e

            except Exception as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ Ошибочка вышла ⚠️\n{str(e)}') from e

    async def send_voice(self, uid):
        while self.retries < self.max_retries:
            try:
                audio_file = open(f"{str(uid)}.wav", "rb")
                result = await self.client.audio.transcriptions.create(model="whisper-1", file=audio_file, temperature=0.1, language="ru")
                return result

            except await self.client.error.RateLimitError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: Превышены лимиты ⚠️\n{str(e)}') from e

            except await self.client.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: кривой запрос ⚠️\n{str(e)}') from e

            except Exception as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ Ошибочка вышла ⚠️\n{str(e)}') from e
