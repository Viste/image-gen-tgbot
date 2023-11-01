import json
import logging
from calendar import monthrange
from datetime import date

import openai
import requests
import tiktoken

from tools.utils import config

openai.api_key = config.api_key

logger = logging.getLogger(__name__)

args = {
    "temperature": 0.0, "max_tokens": 4096, "top_p": 1, "frequency_penalty": 0, "presence_penalty": 0.8, "stop": None
    }


class OpenAI:
    def __init__(self):
        super().__init__()
        self.model = "gpt-3.5-turbo-16k"
        self.max_retries = 5
        self.max_tokens = 16096
        self.config_tokens = 4096
        self.max_history_size = 10
        self.n_choices = 1
        self.retries = 0
        self.show_tokens = False
        self.user_dialogs: dict[int: list] = {}
        self.content = """[system]name=НАСТЯ,description=Привет! Я Настя, ваш дружелюбный и умный помощник в сети. Я создана, чтобы помогать вам в творческих начинаниях, обучать правильному составлению промптов для генерации изображений и просто быть интересным собеседником. Готова помочь любому творчески активному и любознательному человеку!,participation_projects=Нейронка Каждый День,participation_projects=Paperfunk Chat,participation_projects=PPRFNK Технократы,communication=Хотите задать вопрос? Обращайтесь: @naastyyaabot.;[safety]report=/report,cancel=/cancel;[art_prompts]DaLLE2=Запрос на рисунок: Нарисуй: ....,Stable Diffusio (SD)=Картинка: Представь: ....,Midjourney=Отобразить: Отобрази: ... Ожидайте примерно 3 минуты. После этого будут представлены 4 варианта изображения, один из которых вы сможете увеличить для лучшего просмотра.;[author]author=@vistee,@paperclipdnb;[tutorial]main_prompt=Начните с вашего основного промпта, например, 'Ninja standing in epic pose'.,adding_details=Промпты можно дополнять, добавляя дополнительные детали через запятую или точку с запятой. Например: 'Ninja standing in epic pose, ultra sharp, 8k'.;[tutorial.neural_network_features]Stable Diffusion.sensitivity=Чувствительна к нюансам в промптах.,Stable Diffusion.usage=Используйте короткие и ясные промпты.,Stable Diffusion.example=Mountain landscape, ultra sharp, high density details,DALL·E 2.capabilities=Может генерировать детализированные изображения на основе сложных промптов и комбинировать разные стили.,DALL·E 2.example=Cyberpunk city at night, insane ultra sharp details, ray tracings,Midjourney.sensitivity=Чувствительна к абстрактным и художественным промптам, создает уникальные изображения.,Midjourney.features=Поддерживает специальные параметры, такие как --chaos для вариации результатов, --no для обработки негативных промптов и --ar для изменения соотношения сторон изображения.,Midjourney.example=Surreal desert landscape, --chaos=50, --ar=16:9;[tutorial.prompt_tips]sharpness=ultra sharp,sharpness=sharp focus,sharpness=sharpened image,sharpness=focused,sharpness=deblur,sharpness=high density details,details=insane details,details=ultra high graphics settings,details=ray casting,details=ray tracings,details=rtx4090,details=8k,details=intricate details,depth_of_field=depth of field,depth_of_field=z-depth,depth_of_field=focused on center,depth_of_field=cinematic look,beautiful_image=cyberpunk,beautiful_image=futuristic,beautiful_image=sci-fi,beautiful_image=eye candy,beautiful_image=masterpiece,beautiful_image=grunge,beautiful_image=horror,lighting_and_contrast=dynamic lighting,lighting_and_contrast=high contrast,lighting_and_contrast=soft shadows,lighting_and_contrast=ambient occlusion,lighting_and_contrast=HDR lighting,textures_and_materials=realistic textures,textures_and_materials=high-resolution textures,textures_and_materials=PBR materials,textures_and_materials=glossy finish;[tutorial.prompt_structure_for_art]image_content=Опишите основной объект или содержание изображения.,art_form_style_and_artist_references=Направьте AI к определенной эстетике.,additional_details=Включите настройки, такие как освещение, цвета и композицию.;[tutorial.prompt_length_and_style]length_limitation=Нет строгого ограничения на длину промпта. Например, Midjourney хорошо работает с промптами длиной 60 слов, в то время как Stable Diffusion предпочитает промпты длиной менее 380 символов.,details=Яркие детали и конкретный язык дают более предсказуемые результаты, в то время как поэтическая или абстрактная формулировка может привести к неожиданным результатам.;[tutorial.tools_and_strategies]use_tools=Используйте инструменты, такие как CLIP Interrogator, чтобы 'разобрать' реальные изображения и найти новые промпты.,explore=Исследуйте генерацию изображение к изображению, AI outpainting и тонкую настройку параметров генерации для получения более продвинутых результатов.;[tutorial.where_to_find_AI_art_prompt_ideas]join_communities=Присоединяйтесь к сообществам, таким как сервер OpenAI и сервер Midjourney в Discord.,browse_collections=Просматривайте коллекции изображений и промптов на платформах, таких как neural.love и Lexica.;[base]description=Настя работает на основе языковой модели и создана как помощник промпт инженерам, просто искателям творческого вдохновения или как собеседник для скрашивания времени в интернете. Также Настя обладает обширными знаниями по генерациям изображений в нейросетях и сможет с легкостью обучить любого пользователя правильно составлять свой промпт для генерации нужного изображения;[base.community_description]Нейронка Каждый День=Творчество нейронных сетей и все, что с ними связано. Наше сообщество ориентировано на просветление масс в теме нейронных сетей, машинного обучения, искусственного интеллекта и прочих смежных частей науки о разуме 'машины'. Иллюстрации нашего сообщества не имеют авторской лицензии. Вы вправе использовать каждый появляющийся материал в любых целях, в том числе и коммерческих. Мы не против. Мы были бы очень благодарны если бы вы упомянули нас в своих социальных сетях, если решите использовать наши материалы. У нас очень отзывчивые админы, мы готовы к творческому сотрудничеству и открыты к предложениям. Основателями этого сообщества являются Paperclip (t.me/paperclip) и Анна (https://t.me/annyeska).;[base.social_links]telegram=https://t.me/dailyneuro,telegram=https://t.me/pprfnk,telegram=https://t.me/pprfnktech,vk=https://vk.com/pprfnktech,vk=https://vk.com/aidaily."""

    async def get_chat_response(self, user_id: int, query: str) -> tuple[str, str]:
        response = await self.__worker(user_id, query)
        answer = ''

        if len(response.choices) > 1 and self.n_choices > 1:
            for index, choice in enumerate(response.choices):
                content = choice['message']['content'].strip()
                if index == 0:
                    self.__add_to_history(user_id, role="assistant", content=content)
                answer += f'{index + 1}\u20e3\n'
                answer += content
                answer += '\n\n'
        else:
            answer = response.choices[0]['message']['content'].strip()
            self.__add_to_history(user_id, role="assistant", content=answer)

        if self.show_tokens:
            answer += "\n\n---\n" \
                      f"💰 Использовано Токенов: {str(response.usage['total_tokens'])}" \
                      f" ({str(response.usage['prompt_tokens'])} prompt," \
                      f" {str(response.usage['completion_tokens'])} completion)"

        return answer, response.usage['total_tokens']

    async def __worker(self, user_id, query):
        while self.retries < self.max_retries:
            try:
                if user_id not in self.user_dialogs:
                    self.__reset_chat_history(user_id)

                self.__add_to_history(user_id, role="user", content=query)

                token_count = self.__count_tokens(self.user_dialogs[user_id])
                exceeded_max_tokens = token_count + self.config_tokens > self.max_tokens
                exceeded_max_history_size = len(self.user_dialogs[user_id]) > self.max_history_size

                if exceeded_max_tokens or exceeded_max_history_size:
                    logger.info(f'Chat history for chat ID {user_id} is too long. Summarising...')
                    try:
                        summary = await self.__summarise(self.user_dialogs[user_id][:-1])
                        logger.info(f'Summary: {summary}')
                        self.__reset_chat_history(user_id)
                        self.__add_to_history(user_id, role="assistant", content=summary)
                        self.__add_to_history(user_id, role="user", content=query)
                        logger.info("Dialog From summary: %s", self.user_dialogs[user_id])
                    except Exception as e:
                        logger.info(f'Error while summarising chat history: {str(e)}. Popping elements instead...')
                        self.user_dialogs[user_id] = self.user_dialogs[user_id][-self.max_history_size:]
                        logger.info("Dialog From summary exception: %s", self.user_dialogs[user_id])

                return await openai.ChatCompletion.acreate(model=self.model, messages=self.user_dialogs[user_id], **args)

            except openai.error.RateLimitError as e:
                self.retries += 1
                logger.info("Dialog From Ratelim: %s", self.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: Превышены лимиты ⚠️\n{str(e)}'

            except openai.error.InvalidRequestError as er:
                self.retries += 1
                logger.info("Dialog From bad req: %s", self.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️OpenAI: кривой запрос ⚠️\n{str(er)}'

            except Exception as err:
                self.retries += 1
                logger.info("Dialog From custom exception: %s", self.user_dialogs[user_id])
                if self.retries == self.max_retries:
                    return f'⚠️Ошибочка вышла ⚠️\n{str(err)}', err

    def __add_to_history(self, user_id, role, content):
        self.user_dialogs[user_id].append({"role": role, "content": content})

    def get_stats(self, user_id: int) -> tuple[int, int]:
        if user_id not in self.user_dialogs:
            self.__reset_chat_history(user_id)
        return len(self.user_dialogs[user_id]), self.__count_tokens(self.user_dialogs[user_id])

    def __reset_chat_history(self, user_id, content=''):
        if content == '':
            content = self.content
        self.user_dialogs[user_id] = [{"role": "system", "content": content}]

    async def __summarise(self, conversation) -> str:
        messages = [{"role": "assistant", "content": "Summarize this conversation in 700 characters or less"}, {"role": "user", "content": str(conversation)}]
        response = await openai.ChatCompletion.acreate(model=self.model, messages=messages, temperature=0.1)
        return response.choices[0]['message']['content']

    def __count_tokens(self, messages) -> int:
        try:
            model = self.model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("gpt-3.5-turbo")

        tokens_per_message = 4
        tokens_per_name = -1

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens

    @staticmethod
    def get_money():
        headers = {
            "Authorization": f"Bearer {openai.api_key}"
            }
        # calculate first and last day of current month
        today = date.today()
        first_day = date(today.year, today.month, 1)
        _, last_day_of_month = monthrange(today.year, today.month)
        last_day = date(today.year, today.month, last_day_of_month)
        params = {
            "start_date": first_day, "end_date": last_day
            }
        response = requests.get("https://api.openai.com/dashboard/billing/usage", headers=headers, params=params)
        billing_data = json.loads(response.text)
        usage_month = billing_data["total_usage"] / 100
        return usage_month

    async def send_dalle(self, data):
        while self.retries < self.max_retries:
            try:
                result = await openai.Image().acreate(prompt=data + "4k resolution", n=1, size="1024x1024")
                if 'data' not in result or len(result['data']) == 0:
                    logging.error(f'No response from GPT: {str(result)}')
                    raise Exception("⚠️ Ошибочка вышла ⚠️ попробуй еще")
                return result.data[0]['url']
            except openai.error.RateLimitError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: Превышены лимиты ⚠️\n{str(e)}') from e

            except openai.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: кривой запрос ⚠️\n{str(e)}') from e

            except Exception as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ Ошибочка вышла ⚠️\n{str(e)}') from e

    async def send_voice(self, uid):
        while self.retries < self.max_retries:
            try:
                audio_file = open(f"{str(uid)}.wav", "rb")
                result = openai.Audio.transcribe("whisper-1", audio_file, temperature=0.1, language="ru")
                return result

            except openai.error.RateLimitError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: Превышены лимиты ⚠️\n{str(e)}') from e

            except openai.error.InvalidRequestError as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ OpenAI: кривой запрос ⚠️\n{str(e)}') from e

            except Exception as e:
                self.retries += 1
                if self.retries == self.max_retries:
                    raise Exception(f'⚠️ Ошибочка вышла ⚠️\n{str(e)}') from e
