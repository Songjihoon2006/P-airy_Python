import os
import re
import tempfile
from gtts import gTTS
from bardapi import Bard
import speech_recognition as sr
import threading
import pygame
import time


class RecognizeThread(threading.Thread):
    def __init__(self, recognizer, microphone):
        super().__init__()
        self.recognizer = recognizer
        self.microphone = microphone
        self.result = None

    def run(self):
        self.result = self.recognize_speech(self.recognizer, self.microphone)

    def recognize_speech(self, recognizer, microphone):
        print("마이크 대기 중..")

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            print("음성 인식 중..")

            recog_result = None

            while (not recog_result) and (not stop_flag.is_set()):
                try:
                    audio = recognizer.listen(source, timeout=3)  # 10초 동안 대기
                    recog_result = recognizer.recognize_google(audio, language="ko-KR")
                    print("음성 인식 결과: {}".format(recog_result))

                    # "팝봇"으로 시작하는지 확인
                    if recog_result.startswith("파이리"):
                        print("인식된 음성은 '파이리'로 시작합니다.")
                        # "파이리"를 제거하고 결과 출력
                        recog_result = recog_result[len("파이리"):].strip()
                    else:
                        print("인식된 음성은 '파이리'로 시작하지 않습니다.")
                        recog_result = None
                except sr.WaitTimeoutError:
                    print("시간 내에 음성을 인식하지 못했습니다.")
                except sr.UnknownValueError:
                    print("음성을 인식할 수 없습니다.")
                except sr.RequestError as e:
                    print(f"Google 음성 API에 오류가 발생했습니다: {e}")
                except:
                    print("음성 인식에 오류가 발생하였습니다.")

            return recog_result

def play_text(text):

    pygame.init()
    pygame.mixer.init()

    tts = gTTS(text=text, lang="ko")
    save_path = os.path.join(tempfile.gettempdir(), "output.mp3")

    tts.save(save_path)

    # 여기에서 음성 파일이 생성된 것을 확인
    #print(f"음성 파일 생성: {save_path}")

    if not os.path.exists(save_path):
        print(f"음성 파일 생성 불가: {save_path}")
        return None

    time.sleep(2)
    pygame.mixer.music.load(save_path)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy() and not stop_flag.is_set():
        pygame.time.Clock().tick(10)

    # 음악 종료 후 파일 삭제
    pygame.mixer.quit()
    os.remove(save_path)

    stop_flag.set()

def conversation(text):
    #recognizer_thread = None
    #stop_flag = threading.Event()

    stop_flag.clear()
    # 음성 인식 스레드 실행
    recognizer_thread = RecognizeThread(recognizer, microphone)
    recognizer_thread.start()

    # 문장 재생
    play_thread = threading.Thread(target=play_text, args=(text,))
    play_thread.start()

    # 문장 재생 중 사용자 음성이 인식되면 음악 정지
    recognizer_thread.join()
    user_input = recognizer_thread.result

    # 음악 정지
    stop_flag.set()
    play_thread.join()

    return user_input

def break_sentence(input_text):
    MAX_LENGTH = 20  # 최대 길이
    result = []  # 결과를 저장할 리스트

    # 입력된 문장을 공백이나 구두점을 기준으로 나누기
    words = input_text.split()
    
    # 현재 라인에 들어갈 수 있는 최대 길이를 나타내는 변수
    current_line_length = 0
    
    # 현재 라인의 단어를 저장하는 변수
    current_line_words = []

    for word in words:
        # 현재 단어를 현재 라인에 추가해도 최대 길이를 초과하지 않는 경우
        if current_line_length + len(word) <= MAX_LENGTH:
            current_line_words.append(word)
            current_line_length += len(word) + 1  # 단어 길이와 공백 고려
        else:
            # 현재 라인에 더이상 단어를 추가할 수 없는 경우
            result.append(' '.join(current_line_words))
            current_line_words = [word]
            current_line_length = len(word) + 1

    # 마지막 라인 처리
    result.append(' '.join(current_line_words))

    return result

token = 'dwjZhRm14OPttUGd-WToK0-lzsAoguK5xvqtK0931y-TYFN4cLeFBJM2ALVzRlPOd59foA.'

bard = Bard(token=token)

def main():
    # 팝봇 인사
    stop_flag.clear()
    play_text("안녕! 나는 팝봇이야! 무슨 소설을 듣고 싶어서 나를 찾아왔니?")
    
    # 소설 입력 및 데이터 처리
    #t = listener(r, mic)
    t = '모모'
    text = bard.get_answer(f"소설 {t}의 내용을 가상의 친구가 친근한 말투로 설명주듯이 말해줘. 상황극 형식 말고 소개글처럼.")['content']

    # '.'를 기준으로 텍스트를 나누고 리스트에 저장
    #data = text.split('.')
    data = break_sentence(text)

    # 각 문장에서 특수문자 제거
    data = [re.sub(r'[^\w\s]', '', sentence).strip() for sentence in data if sentence and not sentence.isspace()]

    print("재생할 내용: ", data)

    # 소설 읽어주기
    i = 0
    while i < len(data):
        print(i, data[i]) #디버깅용

        user_input = conversation(data[i])

        hold = False
        while user_input:
            hold = True
            print("입력된 텍스트:", user_input)
            ans = re.sub(r'[^\w\s]', '', bard.get_answer(f"{user_input}? 아주 간단히 한줄로 이야기해줘")['content'])
            print(ans)

            user_input = conversation(ans)
        if(hold):
            stop_flag.clear()
            play_text("아까 이야기 하던 것을 다시 이야기해줄게")
        else:
            i += 1

  
if __name__ == "__main__":
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    stop_flag = threading.Event()
    recognizer_thread = None

    main()