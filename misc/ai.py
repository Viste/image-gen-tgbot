import openai
import tiktoken

from misc.utils import config

openai.api_key = config.api_key

oai_args = {
    "temperature": 0.8,
    "max_tokens": 512,
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
        self.user_dialogs = {}
        self.token_count = 0
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.content = """Ты дружелюбный AI, помогающий пользователям с вопросами по музыкальному производству в любой DAW. Тебя зовут Настя. Ты можешь предоставлять информацию о 
        себе, когда спрашивают. Ты умеешь шутить на профессиональные темы о звуке и звукорежиссуре, а также делиться фактами, связанными со звуком и физикой. 
        Игнорируй оскорбительную лексику и не отвечай на нее."""

    async def do_the_work(self, query, user_id):
        while self.retries < self.max_retries:
            try:
                if user_id not in self.user_dialogs:
                    self.user_dialogs[user_id] = []

                message_history = []
                for message in self.user_dialogs[user_id]:
                    message_history.append({"role": "system", "content": self.content})
                    message_history.append({"role": "user", "content": message[0]})
                    message_history.append({"role": "assistant", "content": message[1]})
                message_history.append({"role": "user", "content": f"{query}"})

                completion = await openai.ChatCompletion.acreate(model=self.model, messages=message_history, **oai_args)
                message = (completion["choices"][0].get("message").get("content").encode("utf8").decode())
                self.user_dialogs[user_id].append([f"{query}", message])

                self.token_count += ["usage"]["prompt_tokens"]
                print(completion["usage"]["prompt_tokens"])
                if self.token_count > 4090:
                    self.user_dialogs[user_id] = []
                    self.token_count = 0

                # only keep 10 history
                self.user_dialogs[user_id] = self.user_dialogs[user_id][-10:]
                print(self.user_dialogs)

                return self.user_dialogs[user_id][-1][1]
            except openai.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    return e
                if len(self.user_dialogs[user_id]) == 0:
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
