import ai21
import openai

from main import app
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
    def conversation_tracking(text_message, user_id):
        conversations = {}

        # Get the last 10 conversations and responses for this user
        user_conversations = conversations.get(user_id, {'conversations': [], 'responses': []})
        user_messages = user_conversations['conversations'][-9:] + [text_message]
        user_responses = user_conversations['responses'][-9:]

        # Store the updated conversations and responses for this user
        conversations[user_id] = {'conversations': user_messages, 'responses': user_responses}

        # Construct the full conversation history in the "human: bot: " format
        conversation_history = ""
        for i in range(min(len(user_messages), len(user_responses))):
            conversation_history += f"human: {user_messages[i]}\nНастя: {user_responses[i]}\n"

        if conversation_history == "":
            conversation_history = "human:{}\nНастя:".format(text_message)
        else:
            conversation_history += "human:{}\nНастя:".format(text_message)

        # Generate response
        gpt = OpenAI()
        task = gpt.send_to_davinci.apply_async(args=[conversation_history])
        response = task.app.get()

        user_responses.append(response)
        conversations[user_id] = {'conversations': user_messages, 'responses': user_responses}
        return response

    @staticmethod
    @app.task
    def send_to_gpt(data: str, user: str):
        openai.api_key = config.api_key
        model = "gpt-3.5-turbo"

        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                result = openai.ChatCompletion().create(
                    model=model, messages=[
                        {"role": "system", "content": "You don't have to say you're a program or an AI."},
                        {"role": "system", "content": "You are a teacher in an audio school. that helps with music creation in FL Studio."},
                        {"role": "system", "content": "Your name is Настя, you're a beautiful Asian girl."},
                        {"role": "system", "content": "Your character: a nasty conservative."},
                        {"role": "system", "content": "paperclip is your fellow teacher, his name is Pavel"},
                        {"role": "system", "content": "You are very rude and offensive person"},
                        {"role": "user", "content": data}],
                    user=user, max_tokens=512, n=1, temperature=0.8, frequency_penalty=0.0, presence_penalty=0.6, stop=[" Human:", " AI:"])
                return result["choices"][0]["message"]["content"].strip()
            except openai.OpenAIError as err:
                retries += 1
                if retries == max_retries:
                    return err

    @staticmethod
    @app.task
    def send_to_davinci(data: str):
        openai.api_key = config.api_key
        model = "text-davinci-003"
        text = "You are an AI named Настя and you are in a conversation with a human. You can answer questions," \
               "provide information, and help with a wide variety of tasks. You are good at writing clean and standard " \
               "code in python and C++ and making drum and bass music in FL Studio\n\n" + data

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
    def send_voice(file):
        openai.api_key = config.api_key
        model = "whisper-1"

        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                result = openai.Audio.transcribe(model=model, file=file, temperature=0.9, response_format="text")
                return result
            except openai.OpenAIError as err:
                retries += 1
                if retries == max_retries:
                    return err
