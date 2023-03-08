import openai

from celery import shared_task
from misc.utils import config

openai.api_key = config.api_key


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_jitter=True, retry_kwargs={'max_retries': 5})
def send_davinci(message_text):
    model = "text-davinci-003"
    text = "You are an AI named Настя and you are in a conversation with a human. You can answer questions," \
           "provide information, and help with a wide variety of tasks. You are good at writing clean and standard " \
           "code in python and C++ and making drum and bass music in FL Studio\n\n" + message_text

    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            response = openai.Completion.create(model=model, prompt=text, temperature=0.8, max_tokens=256,
                                                top_p=1, frequency_penalty=0, presence_penalty=0)
            response["choices"][0]["text"].strip()
        except openai.OpenAIError as err:
            retries += 1
            if retries == max_retries:
                return err
