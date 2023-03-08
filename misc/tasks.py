import openai
from celery import shared_task

from misc.utils import config

openai.api_key = config.api_key


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_jitter=True, retry_kwargs={'max_retries': 5})
def get_response(message_list):
    model = "gpt-3.5-turbo"

    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            result = openai.ChatCompletion().create(
                model=model, messages=[{"role": "system", "content": "You don't have to say you're a program or an AI."
                                                                     "You are a teacher in an audio school. that helps with music creation in any DAW."
                                                                     "Your name is Настя, you're a beautiful Asian girl."
                                                                     "You are a strict teacher, but you ignore offensive words because they are not offensive in themselves"},
                                       {"role": "user", "content": "Привет, кто ты?"},
                                       {"role": "assistant", "content": "Я Настя преподаватель в аудиошколе."
                                                                        "которая помогает в создании музыки в любой из DAW."}, ] + message_list,
                max_tokens=512, n=1,temperature=0.7, frequency_penalty=0.0, presence_penalty=0.6)
            return result["choices"][0]["message"]["content"].strip()
        except openai.OpenAIError as err:
            retries += 1
            if retries == max_retries:
                return err

