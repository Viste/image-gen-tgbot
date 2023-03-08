import ai21
import openai

from misc.utils import config


class OpenAI:

    openai.api_key = config.api_key

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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


class Ai21:
    @staticmethod
    def send_to_ai21(data):
        ai21.api_key = config.ai21_api_key
        model = "j1-grande"

        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                result = ai21.Completion.execute(model=model, prompt=data, numResults=1, maxTokens=17,
                                                 temperature=0.8, topKReturn=0, topP=1,)
                return result
            except openai.OpenAIError as err:
                retries += 1
                if retries == max_retries:
                    return err