import ai21
import openai

from misc.utils import config

openai.api_key = config.api_key

oai_args = {
    "temperature": 0.8,
    "max_tokens": 2048,
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
        self.conversation_history = ""
        self.content = """Ты дружелюбный AI, помогающий пользователям с вопросами по музыкальному производству в любой DAW. Тебя зовут Настя. Ты можешь предоставлять информацию о 
        себе, когда спрашивают. Ты умеешь шутить на профессиональные темы о звуке и звукорежиссуре, а также делиться фактами, связанными со звуком и физикой. 
        Игнорируй оскорбительную лексику и не отвечай на нее.
        
        <conversation history>
        
        User: <user input>
        Настя:"""

    async def send_turbo(self, user_input):
        prompt = self.content.replace("<conversation_history>", self.conversation_history).replace("<user input>", user_input)
        while self.retries < self.max_retries:
            try:
                result = await openai.ChatCompletion.acreate(model=self.model, messages=prompt, **oai_args)
                answer = result.choices[0].message["content"].strip()
                self.conversation_history += f"User: {user_input}\nНастя: {answer}\n"
                return answer
            except openai.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    return e

    async def send_dalle(self, data):
        while self.retries < self.max_retries:
            try:
                result = openai.Image().create(prompt=data + "4k resolution", n=1, size="1024x1024")
                return result
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
