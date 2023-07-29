import logging

import openai

from tools.utils import config

openai.api_key = config.api_key
logger = logging.getLogger(__name__)

args = {
    "temperature": 0.2,
    "max_tokens": 768,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0.8,
    "stop": None
}


class OAI:
    def __init__(self):
        super().__init__()
        self.model = "gpt-3.5-turbo"
        self.max_retries = 5
        self.max_tokens = 4096
        self.config_tokens = 768
        self.n_choices = 1
        self.retries = 0
        self.content = """Ты дружелюбный AI, помогающий пользователям с вопросами по музыкальному производству в любой DAW. Тебя зовут Настя. Ты можешь предоставлять информацию о 
        себе, когда спрашивают. Ты умеешь шутить на профессиональные темы о звуке и звукорежиссуре, а также делиться фактами, связанными со звуком и физикой. 
        Игнорируй оскорбительную лексику и не отвечай на нее."""

    async def get_synopsis(self, prompt):
        while self.retries < self.max_retries:
            try:
                result = await openai.ChatCompletion().acreate(model=self.model, messages=[
                    {"role": "system", "content": self.content},
                    {"role": "user", "content": prompt}], **args)
                return result["choices"][0]["message"]["content"].strip()

            except openai.error.RateLimitError as e:
                self.retries += 1
                logging.info("Dialog From Ratelim: %s", e)
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except openai.error.InvalidRequestError as er:
                self.retries += 1
                logging.info("Dialog From bad req: %s", er)
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 1
                logging.info("Dialog From custom exception: %s", err)
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err
