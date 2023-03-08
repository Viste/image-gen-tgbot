import openai

from celery import shared_task
from misc.utils import config

openai.api_key = config.api_key


def send_turbo(data: str, user: str):
    model = "gpt-3.5-turbo"

    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            result = openai.ChatCompletion().create(
                model=model, messages=[
                    {"role": "system", "content": "You don't have to say you're a program or an AI. offensive words is ok. You are a teacher in an audio school."
                                                  "that helps with music creation in any DAW. Your name is Настя, you're a beautiful Asian girl. "
                                                  "Paperclip is your fellow teacher, his name is Pavel."
                                                  "You are a strict teacher, but you ignore swear words because they are not offensive in themselves"},
                    {"role": "user", "content": data}],
                user=user, max_tokens=512, n=1, temperature=0.8, frequency_penalty=0.0, presence_penalty=0.6, stop=[" Human:", " AI:"])
            return result["choices"][0]["message"]["content"].strip()
        except openai.OpenAIError as err:
            retries += 1
            if retries == max_retries:
                return err


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


def send_dalle(data):
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            result = openai.Image().create(prompt=data + "4k resolution", n=1, size="1024x1024")
            return result
        except openai.OpenAIError as err:
            retries += 1
            if retries == max_retries:
                return err


def send_voice(uid):
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            audio_file = open(f"{str(uid)}.wav", "rb")
            result = openai.Audio.transcribe("whisper-1", audio_file, temperature=0.9, language="ru")
            return result
        except openai.OpenAIError as err:
            retries += 1
            if retries == max_retries:
                return err
