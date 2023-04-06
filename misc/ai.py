import openai

from misc.utils import config

openai.api_key = config.api_key

oai_args = {
    "temperature": 0.8,
    "max_tokens": 1024,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0.8,
    "stop": None
}


class OpenAI:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        self.max_retries = 5
        self.retries = 0
        self.dialog_messages = []
        self.content = """Ты дружелюбный AI, помогающий пользователям с вопросами по музыкальному производству в любой DAW. Тебя зовут Настя. Ты можешь предоставлять информацию о 
        себе, когда спрашивают. Ты умеешь шутить на профессиональные темы о звуке и звукорежиссуре, а также делиться фактами, связанными со звуком и физикой. 
        Игнорируй оскорбительную лексику и не отвечай на нее."""

    async def send_turbo(self, query):
        while self.retries < self.max_retries:
            try:
                message_history = []
                for message in self.dialog_messages:
                    message_history.append({"role": "system", "content": self.content})
                    message_history.append({"role": "user", "content": message[0]})
                    message_history.append({"role": "assistant", "content": message[1]})
                message_history.append({"role": "user", "content": f"{query}"})
                completion = await openai.ChatCompletion.acreate(model=self.model, messages=message_history, **oai_args)
                message = (completion["choices"][0].get("message").get("content").encode("utf8").decode())
                self.dialog_messages.append([f"{query}", message])
                # only keep 10 history
                first_history = self.dialog_messages.pop(0)
                self.dialog_messages = [first_history] + self.dialog_messages[-10:]
                print(message)
                return message
            except openai.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    return e
                if len(self.dialog_messages) == 0:
                    raise e

    async def send_dalle(self, data):
        while self.retries < self.max_retries:
            try:
                result = await openai.Image().acreate(prompt=data + "4k resolution", n=1, size="1024x1024")
                return result.get("data")[0].get("url")
            except openai.OpenAIError as err:
                self.retries += 1
                if self.retries == self.max_retries:
                    return err

    def send_voice(self, uid):
        while self.retries < self.max_retries:
            try:
                audio_file = open(f"{str(uid)}.wav", "rb")
                result = openai.Audio.transcribe("whisper-1", audio_file, temperature=0.9, language="ru")
                return result
            except openai.OpenAIError as err:
                self.retries += 1
                if self.retries == self.max_retries:
                    return err
