import logging

from openai import AsyncOpenAI

from tools.utils import config


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
    max_retries: int

    def __init__(self):
        super().__init__()
        self.model = "gpt-4-1106-preview"
        self.client = AsyncOpenAI(api_key=config.api_key, base_url='http://176.222.52.92:9000/v1')
        self.max_retries = 5
        self.max_tokens = 4096
        self.config_tokens = 768
        self.n_choices = 1
        self.retries = 0
        self.content = """ТУТ НАДО ОПИСАТЬ ЛИЧНОСТЬ БОТА ЖЕЛАТЕЛЬНО В json формате(или любой формать ключ-значение), на удивление OPENAI такое воспринимает лучше простого текстовое описание"""

    async def get_synopsis(self, prompt):
        while self.retries < self.max_retries:
            try:
                result = await self.client.ChatCompletion().acreate(model=self.model, messages=[
                    {"role": "system", "content": self.content},
                    {"role": "user", "content": prompt}], **args)
                return result["choices"][0]["message"]["content"].strip()

            except await self.client.error.RateLimitError as e:
                self.retries += 1
                logger.info("Dialog From Ratelim: %s", e)
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except await self.client.error.InvalidRequestError as er:
                self.retries += 1
                logger.info("Dialog From bad req: %s", er)
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 1
                logger.info("Dialog From custom exception: %s", err)
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err
