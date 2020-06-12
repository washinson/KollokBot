import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

import re
from threading import Thread
import random as rnd
import time
import logging as log
import sys

###############################################
# Global variables 
###############################################
def captcha_handler(captcha):
    """ При возникновении капчи вызывается эта функция и ей передается объект
        капчи. Через метод get_url можно получить ссылку на изображение.
        Через метод try_again можно попытаться отправить запрос с кодом капчи
    """

    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()

    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key)

token = open("token.txt").read()
vk_session = vk_api.VkApi(token=token, captcha_handler=captcha_handler)
vk = vk_session.get_api()

log.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=log.INFO)

###############################################
# Utility functions
###############################################
def loadFile(path):
    try:
        f = open(path)
        text = f.read()
        f.close()
        return text
    except Exception as e:
        pass
    return ""

def writeFile(path, text):
    try:
        f = open(path, "w")
        f.write(text)
        f.close()
    except Exception as e:
        pass

def readDefinitions():
    tD = []
    for i in range(1,5):
        try:
            f = open("D_"+str(i)+".txt")
            tD.append([])
            for j in f:
                tD[i-1] += [j]
            f.close()
        except Exception as e:
            print(e)
    return tD

def readTheorems():
    tT = []
    for i in range(1,5):
        try:
            f = open("T_"+str(i)+".txt")
            tT.append([])
            for j in f:
                tT[i-1] += [j]
        except Exception as e:
            print(e)
    return tT

def getRandElement(e):
    i = rnd.randint(0, len(e)-1)
    return e[i], i

def getRandomDefinition(definitions):
    D_num = getRandElement(definitions)
    D_num_num = *getRandElement(D_num[0]),
    return D_num_num[0], D_num[1], D_num_num[1]

def getRandomTheorem(theorems):
    T_num = getRandElement(theorems)
    T_num_num = *getRandElement(T_num[0]),
    return T_num_num[0], T_num[1], T_num_num[1]

###############################################
# Vk functions
###############################################
def askTheorem(peer_id=None, chat_id=None):
    theorem = getRandomTheorem(readTheorems())
    index = 'T' + str(theorem[1] + 1) + '.' + str(theorem[2] + 1)
    vk.messages.send(
        peer_id=peer_id,
        chat_id=chat_id,
        random_id=get_random_id(),
        message="Внезапный коллок!\n"+index+ "\n" + theorem[0]
    )

def askDefinition(peer_id=None, chat_id=None):
    definition = getRandomDefinition(readDefinitions())
    index = 'D' + str(definition[1] + 1) + '.' + str(definition[2] + 1)
    vk.messages.send(
        peer_id=peer_id,
        chat_id=chat_id,
        random_id=get_random_id(),
        message="Внезапный коллок!\n"+index+ "\n" + definition[0]
    )

def askQuestion(types="DT", peer_id=None, chat_id=None):
    if "D" in types: 
        askDefinition(peer_id=peer_id, chat_id=chat_id)
    if "T" in types:
        askTheorem(peer_id=peer_id, chat_id=chat_id)

def askAll():
    log.info("askAll")
    for i in range(1, 15):
        try:
            log.info("Asking " + str(i) + " chat_id")
            askQuestion(types=getRandElement("DT")[0],chat_id=i)
        except Exception as e:
            log.error(e)

def answerTheoremDefinition(text, peer_id):
    log.info("answerTheoremDefinition text=%s peer_id=%s" % (text, peer_id))
    try:
        path = "definitions" if text[0] == 'D' else 'theorems'
        m, n = map(int, text[1:].split('.'))
        path += '/' + str(m) + '/' + str(n - 1) + ".png"

        upload = vk_api.VkUpload(vk_session)
        photo = upload.photo_messages(path, peer_id)[0]

        attachments = ['photo{}_{}'.format(photo['owner_id'], photo['id'])]

        vk.messages.send(
            peer_id=peer_id,
            attachment=','.join(attachments),
            random_id=get_random_id(),
            message=text
        )
    except Exception as e:
        log.error(e)
        return

def answerRand(text, peer_id):
    types = ""
    if "D" in text:
        types += "D"
    if "T" in text:
        types += "T"
    if types == "":
        types = "DT"
    askQuestion(types=types, peer_id=peer_id)

###############################################
# Lifecycle
###############################################
class AskThread(Thread):
    def run(self):
        while True:
            log.info("Ask interation start")
            askAll()
            time.sleep(60*60*2)

class AnswerThread(Thread):
    def run(self):
        log.info("Reading answer requests")
        while True:
            try:
                vk_session = vk_api.VkApi(token=token)
                longpoll = VkBotLongPoll(vk_session, '192336844')
                for event in longpoll.listen():
                    log.info("new event" + str(event.type))
                    if event.type == VkBotEventType.MESSAGE_NEW:
                        log.info('------------')
                        log.info('from ' + str(event.message.from_id))
                        log.info('text ' + str(event.message.text))
                        log.info('peer_id ' + str(event.message.peer_id))
                        log.info('------------')
                        peer_id = event.message.peer_id

                        answerRequest = re.search("[DT]\d\d?\.\d\d?", event.message.text)
                        if answerRequest != None:
                            answerTheoremDefinition(answerRequest.group(0), peer_id=peer_id)
                        
                        randomRequest = re.search("rand(.*D.*T|.*T.*D|.*T|.*D|)", event.message.text)
                        if randomRequest != None:
                            answerRand(randomRequest.group(0), peer_id)
            except Exception as e:
                log.error("Answer error - " + str(e))

###############################################
# The main code
###############################################
AnswerThread().start()
AskThread().start()
while True:
    try:
        command = input().split()
        if command[0] == "help":
            print("send <peer_id> <message>")
        if command[0] == "send":
            vk.messages.send(
                random_id=get_random_id(),
                peer_id=int(command[1]),
                message=" ".join(command[2:])
            )
    except Exception as e:
        print(e)