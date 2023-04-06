import openai
import tiktoken
import logging

from misc.utils import config

openai.api_key = config.api_key
logger = logging.getLogger("__name__")

args = {
    "temperature": 0.8,
    "max_tokens": 512,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0.8,
    "stop": None
}


class OpenAI:
    def __init__(self):
        super().__init__()
        self.model = "gpt-3.5-turbo"
        self.max_retries = 5
        self.max_tokens = 4096
        self.config_tokens = 768
        self.max_history_size = 10
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = True
        self.user_dialogs: dict[int: list] = {}
        self.content = """Ты дружелюбный AI, помогающий пользователям с вопросами по музыкальному производству в любой DAW. Тебя зовут Настя. Ты можешь предоставлять информацию о 
        себе, когда спрашивают. Ты умеешь шутить на профессиональные темы о звуке и звукорежиссуре, а также делиться фактами, связанными со звуком и физикой. 
        Игнорируй оскорбительную лексику и не отвечай на нее."""

    def get_stats(self, user_id: int) -> tuple[int, int]:
        if user_id not in self.user_dialogs:
            self.reset_chat_history(user_id)
        return len(self.user_dialogs[user_id]), self.count_tokens(self.user_dialogs[user_id])

    def reset_chat_history(self, user_id, content=''):
        if content == '':
            content = self.content
        self.user_dialogs[user_id] = [{"role": "system", "content": content}]

    async def summarise(self, conversation) -> str:
        messages = [
            {"role": "assistant", "content": "Summarize this conversation in 700 characters or less"},
            {"role": "user", "content": str(conversation)}
        ]
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
            temperature=0.8
        )
        return response.choices[0]['message']['content']

    def count_tokens(self, messages) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-3.5-turbo")

        tokens_per_message = 4
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

    def add_to_history(self, user_id, role, content):
        self.user_dialogs[user_id].append({"role": role, "content": content})

    async def get_chat_response(self, user_id: int, query: str) -> tuple[str, str]:
        response = await self.do_the_work(user_id, query)
        answer = ''

        if len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                if index == 0:
                    self.add_to_history(user_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        else:
            answer = response.choices[0]['message']['content'].strip()
            self.add_to_history(user_id, role="assistant", content=answer)

        if self.show_tokens:
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage['total_tokens'])}" \
                      f" ({str(response.usage['prompt_tokens'])} prompt," \
                      f" {str(response.usage['completion_tokens'])} completion)"

        return answer, response.usage['total_tokens']

    async def do_the_work(self, query, user_id):
        while self.retries < self.max_retries:
            try:
                if user_id not in self.user_dialogs:
                    self.reset_chat_history(user_id)

                self.add_to_history(user_id, role="user", content=query)

                token_count = self.count_tokens(self.user_dialogs[user_id])
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(self.user_dialogs[user_id]) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logging.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self.summarise(self.user_dialogs[user_id][:-1])
                        logging.debug(f'Summary: {summary}')
                        self.reset_chat_history(user_id)
                        self.add_to_history(user_id, role="assistant", content=summary)
                        self.add_to_history(user_id, role="user", content=query)
                    except Exception as e:
                        logging.warning(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        self.user_dialogs[user_id] = self.user_dialogs[user_id][-self.max_history_size:]

                return await openai.ChatCompletion.acreate(model=self.model, messages=self.user_dialogs[user_id], **args)

            except openai.error.RateLimitError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: Превышены лимиты ⚠️\n{str(e)}') from e

            except openai.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: кривой запрос ⚠️\n{str(e)}') from e

            except Exception as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ Ошибочка вышла ⚠️\n{str(e)}') from e

    async def send_dalle(self, data):
        while self.retries < self.max_retries:
            try:
                result = await openai.Image().acreate(prompt=data + "4k resolution", n=1, size="1024x1024")
                return result.get("data")[0].get("url")
            except openai.error.RateLimitError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: Превышены лимиты ⚠️\n{str(e)}') from e

            except openai.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: кривой запрос ⚠️\n{str(e)}') from e

            except Exception as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ Ошибочка вышла ⚠️\n{str(e)}') from e

    def send_voice(self, uid):
        while self.retries < self.max_retries:
            try:
                audio_file = open(f"{str(uid)}.wav", "rb")
                result = openai.Audio.transcribe("whisper-1", audio_file, temperature=0.9, language="ru")
                return result

            except openai.error.RateLimitError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: Превышены лимиты ⚠️\n{str(e)}') from e

            except openai.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: кривой запрос ⚠️\n{str(e)}') from e

            except Exception as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ Ошибочка вышла ⚠️\n{str(e)}') from e
