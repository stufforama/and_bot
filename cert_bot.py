
# coding: utf-8

# In[2]:

print('importing')
import numpy as np
import pandas as pd
import re
import urllib
import telebot
import googlemaps



# In[ ]:

#информация о свидетельствах
print('loadind certificates')
data = pd.read_csv(r'doclist.csv', delimiter= ";", header=None, encoding = 'utf8')
data.columns = ['text', 'url']
pattern = '-[0-9]{3,4}'
data['sku'] = data['text'].apply(lambda x: re.findall(string=x, pattern = pattern)[0].rsplit('-')[1])
data['start'] = data['text'].apply(lambda x: re.findall(string=x, pattern = '[0-9]{6,}')[0])
data['end'] = data['text'].apply(lambda x: re.findall(string=x, pattern = '[0-9]{6,}')[1])
data['start'] = pd.to_numeric(data['start'])
data['end'] = pd.to_numeric(data['end'])
data['url'] = data['url'].apply(lambda x: 'http://' + urllib.parse.quote(x.rsplit('//')[1]))

#информация о сервисных центрах
print('loadind service centeres')
services = pd.read_csv(r'service.csv', encoding='utf8', index_col=0)
services.drop(['geocode', 'address'], axis=1,inplace=True)
services['workhours'].fillna('', inplace = True)
useful_cols = ['city', 'type', 'address1', 'address2', 'tel', 'workhours']

#словарь видеоинструкций
print('loadind manuals list')
manuals = {'Автоматический тонометр':'https://youtu.be/nTWcDJGSiwo', 
           'Компрессорный ингалятор':'https://youtu.be/JY1urhMFnTg',
           'Электронный термометр': 'https://youtu.be/iA6yIxAYawE'}

#googlemaps
print('loadind gmaps')
API_KEY = 'AIzaSyAau5W4033f5PotzAw-DpK0DwmhHlQ1HFY'
gmaps = googlemaps.Client(key=API_KEY)

#инициализируем бота
print('Running bot')
token = '431029921:AAEpcAygl-U9wf0Dh0mQf0hBkgi_rAxejAs'
bot = telebot.TeleBot(token)

func_list = ['Информация о поверке', 'Ближайший сервисный центр', 'Видеоинструкции']
keyboard_layout = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
for func in func_list:
    keyboard_layout.add(func)

start_msg = 'Чем я могу помочь?'

# global last_message
last_message = ''

def nearest_service(location):
    min_dist = 10000000
    nearest_sc = ''
    sc_description = ''
    for index in range(services.shape[0]):
        distance = np.sqrt((location.latitude-services.lat[index])**2 + (location.longitude-services.lng[index])**2)
        if distance < min_dist:
            min_dist = distance
            nearest_sc = index
    sc_longitude = services['lng'].loc[nearest_sc]
    sc_latitude = services['lat'].loc[nearest_sc]
    sc_description = '\n'.join(list(services[useful_cols].loc[nearest_sc]))
    return sc_longitude, sc_latitude, sc_description    

def manual_nearest_service(lat, lng):
    min_dist = 10000000
    nearest_sc = ''
    sc_description = ''
    for index in range(services.shape[0]):
        distance = np.sqrt((lat-services.lat[index])**2 + (lng-services.lng[index])**2)
        if distance < min_dist:
            min_dist = distance
            nearest_sc = index
    sc_longitude = services['lng'].loc[nearest_sc]
    sc_latitude = services['lat'].loc[nearest_sc]
    sc_description = '\n'.join(list(services[useful_cols].loc[nearest_sc]))
    return sc_longitude, sc_latitude, sc_description  

@bot.message_handler(commands=["start", 'menu'])
def dial_start(message):
    bot.send_message(message.chat.id, start_msg, reply_markup = keyboard_layout)
        

@bot.message_handler(content_types=['text', 'location'])
def response(message):
    global last_message
    geo_request = 'Пожалуйста, укажите свой город и адрес'
    sn_request = 'Введите серийный номер в формате [Модель][пробел][Серийный номер]'
    check_sn = 'Проверьте правильность ввода'
    manual_request = 'Выберите интересующую катеорию'
    if message.text == 'Информация о поверке':
        markup = telebot.types.ForceReply(selective=False)
        bot.send_message(message.chat.id, sn_request, reply_markup=markup)
        last_message = sn_request
    elif message.text == 'Ближайший сервисный центр':
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button_geo = telebot.types.KeyboardButton(text="Определить автоматически", request_location=True)
        markup.add(button_geo)
        bot.send_message(message.chat.id, geo_request, reply_markup=markup)   
        last_message = geo_request
    elif message.text == 'Видеоинструкции':
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button_man_ton = telebot.types.KeyboardButton(text="Автоматический тонометр")
        button_man_ing = telebot.types.KeyboardButton(text="Компрессорный ингалятор")
        button_man_therm = telebot.types.KeyboardButton(text="Электронный термометр")
        markup.add(button_man_ton)
        markup.add(button_man_ing)
        markup.add(button_man_therm)
        bot.send_message(message.chat.id, manual_request, reply_markup=markup)   
        last_message = manual_request
    elif message.text in manuals:
        bot.send_message(message.chat.id, manuals[message.text], reply_markup = keyboard_layout)
        last_message = manuals[message.text]
    elif message.reply_to_message != None:
        if (message.reply_to_message.text == sn_request) | (message.reply_to_message.text == check_sn):
            try:
                sku = re.findall(string=message.text, pattern = '[0-9]{3,4}')[0]
                serian_number = int(''.join(re.findall(string=message.text, pattern = '[0-9]{4,}')[-2:]))
                fltr = data.loc[(data['sku']==sku)&(data['start']<=serian_number)&(data['end']>=serian_number)]['url'].max()
                if str(fltr) != 'nan':
                    response = fltr
                    bot.send_message(message.chat.id, response, reply_markup = keyboard_layout)
                else:
                    response = check_sn
                    markup = telebot.types.ForceReply(selective=False)
                    bot.send_message(message.chat.id, response, reply_markup = markup)
            except IndexError:
                response = check_sn
                markup = telebot.types.ForceReply(selective=False)
                bot.send_message(message.chat.id, response, reply_markup = markup)
            last_message = response
    elif message.location != None:
        nearest_sc_longitude, nearest_sc_latitude, nearest_sc_descr = nearest_service(message.location)
        bot.send_message(message.chat.id, nearest_sc_descr)
        bot.send_location(message.chat.id, longitude=nearest_sc_longitude, latitude=nearest_sc_latitude,  reply_markup=keyboard_layout)
        last_message = nearest_sc_descr       
    elif (last_message == geo_request) & (message.location == None):
        try:
            manual_location = message.text
            geocode = gmaps.geocode(manual_location)
            manual_lat = geocode[0]['geometry']['location']['lat']
            manual_lng = geocode[0]['geometry']['location']['lng']
            nearest_sc_longitude, nearest_sc_latitude, nearest_sc_descr = manual_nearest_service(manual_lat, manual_lng)
            bot.send_message(message.chat.id, nearest_sc_descr)
            bot.send_location(message.chat.id, longitude=nearest_sc_longitude, latitude=nearest_sc_latitude,  reply_markup=keyboard_layout)
            last_message = nearest_sc_descr
        except IndexError:
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            button_geo = telebot.types.KeyboardButton(text="Определить автоматически", request_location=True)
            markup.add(button_geo)
            bot.send_message(message.chat.id, geo_request, reply_markup=markup)   
            last_message = geo_request
       
if __name__ == '__main__':
     bot.polling(none_stop=True)
