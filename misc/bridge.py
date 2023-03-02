import openai
import ai21

from misc.utils import config


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


class OpenAI:
    @staticmethod
    def send_to_gpt(data):
        openai.api_key = config.api_key
        model = "gpt-3.5-turbo"

        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                result = openai.ChatCompletion().create(model=model, messages=[{"role": "user", "content": data}],
                                                        max_tokens=512, n=1, temperature=0.9, frequency_penalty=0.0,
                                                        presence_penalty=0.6, stop=[" Human:", " AI:"])
                return result
            except openai.OpenAIError as err:
                retries += 1
                if retries == max_retries:
                    return err

    @staticmethod
    def send_to_dalle(data):
        openai.api_key = config.api_key
        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                result = openai.Image().create(prompt=data, n=1, size="1024x1024")
                return result
            except openai.OpenAIError as err:
                retries += 1
                if retries == max_retries:
                    return err

    @staticmethod
    def send_voice(data):
        openai.api_key = config.api_key
        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                result = openai.Audio.transcribe("whisper-1", data, temperature=0.9, response_format="text")
                return result
            except openai.OpenAIError as err:
                retries += 1
                if retries == max_retries:
                    return err
