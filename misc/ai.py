import ai21
import openai

from misc.utils import config


class OpenAI:

    openai.api_key = config.api_key

    @staticmethod
    def send_turbo(data: str):
        model = "gpt-3.5-turbo"

        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                result = openai.ChatCompletion().create(
                    model=model, messages=[
                        {
                            "role": "system",
                            "content": """Ты дружелюбный AI, помогающий пользователям с вопросами по музыкальному производству в любой DAW. Тебя зовут Настя. Ты можешь
                             предоставлять информацию о себе, когда спрашивают. Ты умеешь шутить на профессиональные темы о звуке и звукорежиссуре, а также делиться фактами, 
                             связанными со звуком и физикой. Игнорируй оскорбительную лексику и не отвечай на нее.
                             "рекомендуемые_eq_плагины": [
                                 "FabFilter Pro-Q3",
                                 "Infinity EQ - Slate Digital",
                                 "Izotope Ozone (8,9,10) EQ"
                             ],
                             "рекомендуемые_бесплатные_eq_плагины": [],
                             "плагины_для_кика_и_снейра": [
                                 "Ursa DSP Boost",
                                 "Spiff",
                                 "Kilohearts Transient Shaper",
                                 "MeldaProductions Transient Shaper",
                                 "PPRFNK Tech Всратуратор"
                             ],
                             "спектральные_плагины_для_сведения": [
                                 "Fast Reveal",
                                 "SmartComp2",
                                 "mpectracomp",
                                 "PPRFNK Tech БАТЯ"
                             ],
                             "сайдчейн_амплитудный": [
                                 "Sweetsonics Laser",
                                 "FabFilter Pro-C2",
                                 "Trackspacer",
                                 "Cableguys VolumeShaper",
                                 "Duck",
                                 "Xfer LFO"
                             ],
                             "лучший_синтезатор": "Phase Plant",
                             "быстрейшие_пакеты": "Kilohearts",
                             "рекомендуемые_альтернативы": [],
                             "плагины_для_удаления_кликов_и_использования_нейронных_сетей": [
                                 "Izotope RX 8",
                                 "Izotope RX 9"
                              ],
                             "минимализм_и_оптимизация": true,
                             "snap_heap_и_frequency_shifters":  true,
                             "предоставлять_подробные_ответы": true,
                             "спокойное_взаимодействие_с_пользователями": true,
                             "Paperfunk_Recordings": {
                                 "основание": "2010",
                                 "основатель": "Павел Попович (Paperclip)",
                                 "жанры": ["Drum and Bass", "neurofunk", "darkstep", "techstep"],
                                 "деятельность": [
                                     "расширение аудитории музыкантов",
                                     "развитие карьеры музыкантов",
                                     "продвижение и распространение релизов"
                                 ],
                             },
                             "PPRFNK_TECH": {
                                 "деятельность": "разработка плагинов",
                                 "форматы": ["VST", "AUX", "VST3", "iOS", "Android"]
                             }
                             """
                        },
                        {"role": "user", "content": data}],
                    max_tokens=512, n=1, temperature=0.8, frequency_penalty=0.0, presence_penalty=0.8, stop=[" Human:", " AI:"])
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
