#importing vk_api modules + keys:
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
#mongodb lib importing:
import pymongo
#other libs:
import random
import datetime
import threading

#defs:
def what_work(work):
    if (work == 0):
        work = 'Безработный'
    elif (work == 1):
        work = 'Уборщик'
    elif(work == 2):
        work = 'Машинист'
    elif(work == 3):
        work = 'Управляющий'
    return work

def run_in_thread(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.start()
    return run

@run_in_thread
def wait(id):
    import time
    profile = find_data(collection=users, data={"id": id})
    cooldown = int(profile['cooldown'])
    x = 0
    while(cooldown != x):
        profile = find_data(collection=users, data={"id": id})
        cooldown = int(profile['cooldown'])
        if(cooldown == 0):
            break
        cooldown -= 2
        time.sleep(2)
        update_data(collection=users, id=id, new_values={'cooldown': cooldown})

def update_data(collection, id, new_values):  # update data in mongodb collection
    collection.update_one({'id': id}, {'$set': new_values})


def insert_data(collection, data):  # for data inserting to mongodb collection
    return collection.insert_one(data).inserted_id


def find_data(collection, data, multiple=False):  # serching data in mongodb collection
    if multiple:  # if you didn't set multiple var as True, it'll be False at default
        results = collection.find(data)
        return [r for r in results]
    else:
        return collection.find_one(data)


def delete_data(collection, id, data=None, multiple=False):
    if multiple:  # if you didn't set multiple var as True, it'll be False at default
        results = collection.deleteMany(data)
        return [r for r in results]
    else:
        return collection.deleteOne({"id": int(id)})

def send(msg=None, attachment=None, keyboard=None, id=None, uid = None):
    if(id == None):
        vk.messages.send(user_id=uid,
                         message=msg,
                         attachment=attachment,
                         keyboard=keyboard,
                         random_id=random.randint(-2147483648, +2147483648))
    else:
        vk.messages.send(peer_id=id,
                         message=msg,
                         attachment=attachment,
                         keyboard=keyboard,
                         random_id=random.randint(-2147483648, +2147483648))
        return 0


def create_keys():
    keyboard = VkKeyboard(one_time=False, inline=True)
    keyboard.add_button('?', color=VkKeyboardColor.DEFAULT)
    keyboard.add_button('profile', color=VkKeyboardColor.DEFAULT)
    keyboard.add_button('work', color=VkKeyboardColor.DEFAULT)
    keyboard = keyboard.get_keyboard()
    return keyboard

#vars and connect to VK and mongo:
client = pymongo.MongoClient('localhost', 27017)#make connect to mongodb
db = client['UsersDB']#get db
users = db['users']#get collection of users
secret = db['secrets']
vk_token = find_data(collection=secret, data={"id": 0})
if(vk_token == None):
    token = input('Введите Ваш токен для записи в БД: ')
    insert_data(collection=secret, data={"id": 0,
                                         "token": token
                                         })
else:
    token = vk_token['token']
#token = '2516743fae6542e7bfac0084c7a5e28deb90871142c166eaf01ee0f5c2be0b03ef40c3b07fabde08a6161'#VK Group Token
vk_session = vk_api.VkApi(token=token)#Connecting to VK
longpoll = VkLongPoll(vk_session)#Set longpoll session
vk = vk_session.get_api()#Get api session
keys = create_keys()

send(msg='Запуск бота успешен! Начинаю работу! \nТокен: ' +token)

#starting longpoll listener:
while (1 == 1):
    for event in longpoll.listen():#every longpoll event'll be in var event
        try:
            if (event.type == VkEventType.MESSAGE_NEW): #if type of event is new message
                text = event.text.lower()#make text lower
                text = text.split()#split text for ' '
                if not(event.from_me):#check if message from group
                    try:
                        profile = find_data(collection=users, data={"id": event.user_id})
                        cooldown = int(profile['cooldown'])
                        usr_id = profile["id"]
                        name = profile["name"]
                        balance = int(profile["balance"])
                        perms = profile['perms']
                        time = profile['regtime']
                        work = int(profile['work'])
                        max = profile['max']
                        work = what_work(work)
                        hmw = int(profile['hmw'])
                        try:
                            usr_id = text[1]
                            usr_profile = find_data(collection=users, data={"id": int(usr_id)})
                            cooldown = profile['cooldown']
                            usr_id = profile["id"]
                            name = profile["name"]
                            balance = profile["balance"]
                            perms = profile['perms']
                            time = profile['regtime']
                            work = int(profile['work'])
                            max = profile['max']
                            work = what_work(work)
                        except:
                            pass
                    except:
                        pass
                    try:
                        isBanned = profile['isBanned']
                        if(isBanned == 1):
                            send(msg='Вы были заблокированы в данном боте! Обратитесь к @karagozov (админу)!', id=event.peer_id)
                            continue
                        else:
                            pass
                    except:
                        pass
                    try:
                        if(int(profile['balance']) < 0):
                            update_data(collection=users, id=event.user_id, new_values={"balance": 0})
                            send(id=event.peer_id, msg='Ваш баланс меньше 0 из-за ошибки. Ваш баланс обнулён. Приятной игры!')
                            profile = find_data(collection=users, data={"id": event.user_id})
                    except:
                        pass
                    if((text[0] == 'профиль') or (text[0] == 'profile')):
                        vk_profile = vk.users.get(user_ids = str(event.user_id), fields='screen_name')
                        profile = find_data(collection=users, data={"id": int(event.user_id)})
                        if(profile == None):
                            time = datetime.datetime.now()
                            time = time.strftime("%d-%m-%Y %H:%M")
                            insert_data(collection=users, data={"id": event.user_id,
                                                                "name": vk_profile[0]['first_name'],
                                                                "balance": 10000,
                                                                "scr_nm": vk_profile[0]['screen_name'],
                                                                "perms": 0,
                                                                "isBanned": 0,
                                                                "regtime": time,
                                                                "cooldown": 0,
                                                                "work": 0,
                                                                "work_perms": 0,
                                                                "hmw": 0,
                                                                "max": 1
                                                                })

                            send(id=event.peer_id, msg='Вы успешно зарегестрированы!')
                        else:
                            if(perms == 0):
                                perms = 'Игрок'
                            else:
                                perms = 'Admin'
                            if(int(usr_id) == 457450528):
                                perms = 'Баг-тестер'
                            isBanned = profile['isBanned']
                            if(isBanned == 1):
                                isBanned = '1 блокировка AAC'
                            else:
                                isBanned = 'Активных блокировок нет'
                            #e.t.c
                            send(id=event.peer_id, msg=
                            'Ваш профиль:' +
                            '\nИмя: ' + name + '(' + perms + ')' +
                            '\nVK ID: ' + str(usr_id) +
                            '\nБаланс: ' + str(balance) +
                            '\nРабота: ' + work + ' ' + str(max) + ' уровня' +
                            '\n' + isBanned +
                            '\n\nДата регистрации: ' + time
                            )
                    elif((text[0] == 'рандом') or (text[0] == 'random')):
                        avl_sum = int(profile['balance'])
                        try:
                            avl_sum = int(balance)
                            sum = int(text[1])
                            if((int(avl_sum < sum)) or (sum == 0) or (sum < 0)):
                                send(msg='Ваш баланс мал для данной ставки! Доступная сумма: ' + str(avl_sum))
                                continue
                            balance = profile['balance']
                            balance -= sum
                            status = random.randint(1,100)

                            if(status <= 30):
                                sum = sum * 2
                                balance += sum
                                update_data(collection=users, id=event.user_id, new_values={"balance": balance})
                                send(msg='Вы выйграли, поздравляю! Ваша ставка умножается на 2. Ваш баланс: ' + str(balance), id=event.peer_id)
                            else:
                                send(id=event.peer_id, msg='Вы проиграли! Ваш баланс: ' + str(balance))
                                update_data(collection=users, id=event.user_id, new_values={"balance": balance})
                        except:
                            send(msg='Вы допустили ошибку или ваш баланс мал для данной ставки! Доступный баланс: ' + str(avl_sum), id=event.peer_id)

                    elif((text[0] == 'give') or (text[0] == 'выдать')):
                        try:
                            user_id = int(text[1])
                            sum = text[2]
                            if((str(event.user_id) == '201464141') or (str(profile['perms']) == '1')):
                                balance = int(balance) + int(sum)
                                update_data(collection=users, id=user_id, new_values={"balance": balance})
                                send(msg='Баланс успешно выдан, сумма на данный момент: ' + str(balance), id=event.peer_id)
                                send(msg='@' + name +'(Админом)' + ' вам было выдано ' + str(sum) + '. Ваш баланс: ' +str(balance), uid=user_id)
                            else:
                                send(msg='Псс, чел, команда то только для админов :)', id=event.peer_id)
                        except:
                            if((str(event.user_id) == '201464141') or (str(profile['perms']) == '1')):
                                send(msg='Вы допустили ошибку! Правильное написание: выдать [id] [сумма]', id=event.peer_id)
                            else:
                                send(msg='Псс, чел, команда то только для админов :)', id=event.peer_id)

                    elif((text[0] == 'check') or (text[0] == 'найти')):
                        if((str(event.user_id) == '201464141') or (str(profile['perms']) == '1')):
                            try:
                                user_id = text[1]
                                if (perms == 0):
                                    perms = 'Игрок'
                                else:
                                    perms = 'Admin'
                                if (int(usr_id) == 457450528):
                                    perms = 'Баг-тестер'
                                isBanned = profile['isBanned']
                                if (isBanned == 1):
                                    isBanned = '1 блокировка AAC'
                                else:
                                    isBanned = 'Активных блокировок нет!'
                                send(id=event.peer_id, msg=('Профиль @' + scr_nm +'(' + name + ')' +
                                                       '\nИмя: ' + name +
                                                       '(' + perms + ')' + '\nVK ID: ' + str(usr_id) +
                                                       '\nБаланс: ' + str(balance) +
                                                        '\n' + isBanned,
                                                        '\nДата регистрации: ' + time))
                            except:
                                if((str(event.user_id) == '201464141') or (str(profile['perms']) == '1')):
                                    send(msg='Вы допустили ошибку! Правильное написание: найти [id]', id=event.peer_id)
                                else:
                                    send(msg='Псс, чел, команда то только для админов :)', id=event.peer_id)

                    elif(text[0] == 'setadmin'):
                        if (str(event.user_id) == '201464141'):
                            try:
                                if(str(perms) == '1'):
                                    send(msg='У данного пользователя уже есть админ-права!', id=event.peer_id)
                                else:
                                    send(msg='Админ-права выданы!', id = event.peer_id)
                                    update_data(collection=users, id=int(usr_id), new_values={"perms": 1})
                                    send(msg='@' + name +'(Админом)' + ' вам были выданы админ-права!', uid=int(usr_profile["id"]))

                            except:
                                send(msg='Андрюх, чет не так ввел, исправь :)', id=event.peer_id)

                    elif(text[0] == 'removeadmin'):
                        if (str(event.user_id) == '201464141'):
                            try:
                                if(str(perms) == '0'):
                                    send(msg='У данного пользователя нет админ-прав!', id=event.peer_id)
                                else:
                                    send(msg='Админ-права сняты!', id = event.peer_id)
                                    send(msg='@' + name +'(Админом)' + ' вам были сняты админ-права!', uid=int(usr_profile["id"]))
                                    update_data(collection=users, id=int(usr_id), new_values={"perms": 0})

                            except:
                                send(msg='Андрюх, чет не так ввел, исправь :)', id=event.peer_id)


                    elif((text[0] == 'balance') or (text[0] == 'баланс')):
                        balance = profile['balance']
                        send(msg='Ваш баланс: ' + str(balance), id = event.peer_id)

                    elif(text[0] == 'ban'):
                        try:
                            if((str(event.user_id) == '201464141') or (str(profile['perms']) == '1')):
                                if((int(usr_profile['isBanned'] == 1)) or (int(usr_profile['id']) == 201464141)):
                                    send(msg='Данный человек уже забанен или является создателем!', id = event.peer_id)
                                else:
                                    send(msg='Человек успешно забанен!', id=event.peer_id)
                                    send(msg='@' + name + '(Админом)' + ' вы были забанены!', uid=str(usr_profile["id"]))
                                    update_data(collection=users, id=int(usr_id), new_values={"isBanned": 1})
                        except:
                            send(msg='Вы допустили ошибку! Правильное написание: ban [id]', id=event.peer_id)

                    elif(text[0] == 'unban'):
                        try:
                            if((str(event.user_id) == '201464141') or (str(profile['perms']) == '1')):
                                if(isBanned == 0):
                                    send(msg='Данный человек не имеет блокировки!', id = event.peer_id)
                                else:
                                    send(msg='Человек успешно разбанен!', id=event.peer_id)
                                    send(msg='@' + name + '(Админом)' + ' вы были разбанены!', uid=str(usr_profile["id"]))
                                    update_data(collection=users, id=int(usr_id), new_values={"isBanned": 0})
                        except:
                            send(msg='Вы допустили ошибку! Правильное написание: unban [id]', id=event.peer_id)

                    elif((text[0] == '?') or (text[0] == 'помощь') or (text[0] == 'help')):
                        send(''' 
                        Помощь:
                        Профиль - твой игровой профиль,
                        Баланс - твой баланс,
                        Рандом [сумма] - в случае выйгрыша ваша ставка *2, в случае проигрыша снимается с баланса,
                        Работа 1 - устроиться на работу,
                        Работа(ть) - работать на работе
                        ''', keyboard=keys, id = event.peer_id)

                    elif((text[0] == 'work') or (text[0] == 'работа') or (text[0] == 'работать')):
                        work = profile['work']
                        wt_w = what_work(work)
                        try:
                            ulw = int(text[1])
                            try:
                                if(ulw == 1):
                                    update_data(collection=users, id=int(profile["id"]), new_values={"work": 1})
                                    send(msg='Вы успешно устроены на должность уборщика! \nПроработайте на ней 4 раза, чтобы получить доступ к след. работе', id = event.peer_id)
                                else:
                                    send(msg='Ошибка в написании команды! Правильное написание: работа [название работы]', id=event.peer_id)
                            except:
                                send(msg='Ошибка в выборе работы', id=event.peer_id)
                        except:
                            if(cooldown == 0):
                                if(work == 0):
                                    send(msg='Вы не устроены на работу!', id=event.peer_id)
                                elif(work == 1):
                                    hmw = int(profile['hmw'])
                                    balance = int(profile['balance'])
                                    hmw += 1
                                    send(msg='Вы успешно поработали!', id=event.peer_id)
                                    balance += 1000
                                    update_data(collection=users, id=int(profile['id']), new_values={'hmw': hmw,
                                                                                                     'balance': balance
                                                                                                     })
                                    if(int(hmw) == 4):
                                        send(msg='Вы успешно устроены на след. работу! На ней вы устаёте сильнее!', id=event.peer_id)
                                        print('f')
                                        wait(id = int(usr_id))
                                        print('f')
                                        update_data(collection=users, id=int(profile['id']), new_values={'cooldown': 60*15,
                                                                                                         "work": 2
                                                                                                         })
                                        print('f')
                                elif (work == 2):
                                    hmw = int(hmw)
                                    hmw += 1
                                    send(msg='Вы успешно поработали!', id=event.peer_id)
                                    balance += 5000
                                    update_data(collection=users, id=int(profile['id']), new_values={'hmw': hmw,
                                                                                                     'balance': balance
                                                                                                     })
                                    if (int(hmw) == 20):
                                        send(msg='Вы успешно устроены на след. работу! На ней вы устаёте сильнее!', id=event.peer_id)
                                        update_data(collection=users,
                                                    id=int(profile['id']),
                                                    new_values={'cooldown': 60 * 20,
                                                                "work": 3
                                                                }
                                                    )
                                        wait(id=int(profile['id']))

                                elif (work == 3):
                                    hmw = int(hmw)
                                    hmw += 1
                                    send(msg='Вы успешно поработали!', id=event.peer_id)
                                    balance += 50000
                                    update_data(collection=users, id=int(profile['id']), new_values={'hmw': hmw,
                                                                                                     'balance': balance
                                                                                                     })
                                    if (int(hmw) == max):
                                        send(msg='Уровень работы успешно повышен. Теперь Вам надо отработать: ' + str(max) + ' раз', id=event.peer_id)
                                        max += 1
                                        update_data(collection=users,
                                                    id=int(profile['id']),
                                                    new_values={'cooldown': 60 * 40,
                                                                "max": max
                                                                }
                                                    )
                                        wait(id=int(profile['id']))

                            else:
                                send(msg='Вы не можете работать, ожидайте ' + str(int(cooldown/60)) + ' мин!', id=event.peer_id)

                    elif((text[0] == 'купить') or (text[0] == 'buy')):
                        if(text[1] == 'энергетик'):
                            if(int(balance) > 10000):
                                balance -= 10000
                                send(msg='Энергетик куплен!', id=event.user_id)
                                update_data(collection=users, id=int(usr_id), new_values={"cooldown": 0})


                else:#this'll be done if message from your group
                    pass#just pass and do nothing
        except:
            pass