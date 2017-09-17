import telebot
import time
import requests
import unicodedata
import datetime
from lxml import html
from random import randint

TOKEN = *******************
tb = telebot.TeleBot(TOKEN)

url_ayu = 'http://www.vitoria-gasteiz.org'
meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
categorias = [["teatro"],["familiar", "infantil"],["visitas", "visita guiada", "visita"],["cine", "cines", "pelicula", "proyeccion"],["musica", "concierto", "banda" ,"bailables", "bailes"],["mercado"],["festival", "magialdia", "festval"] ["comision"] ["paseos", "paseo", "recorrido"]]

lng = 'es'

#para que solo sea privado func=lambda message: message.chat.type == 'private')

def process_message(message):
    msg = message.lower()
    msg = ''.join((c for c in unicodedata.normalize('NFD', msg) if unicodedata.category(c) != 'Mn'))

    for i, mes in enumerate(meses):
        msg.replace(mes, "/" + str(i) + "/")

    msg = msg.replace("hoy", time.strftime(" %d/%m/%Y "))
    msg = msg.replace("mañana", (datetime.date.today() + datetime.timedelta(days=1)).strftime(" %d/%m/%Y "))
    msg = msg.replace("pasado", (datetime.date.today() + datetime.timedelta(days=2)).strftime(" %d/%m/%Y "))
    msg = msg.replace("esta semana", time.strftime(" %d/%m/%Y ")+" "+(datetime.date.today() + datetime.timedelta(days=7)).strftime(" %d/%m/%Y "))
    msg = msg.replace("ahora", time.strftime(" %H:%M "))#(datetime.now() - datetime.timedelta(minutes=1)).strftime(" %H:%M ")+" "+ (datetime.now() + datetime.timedelta(hours=1)).strftime(" %H:%M "))
    msg = msg.replace("a esta hora", (datetime.datetime.now() - datetime.timedelta(minutes=30)).strftime(" %H:%M ")+" "+ (datetime.datetime.now() + datetime.timedelta(minutes=30)).strftime(" %H:%M "))
    msg = msg.replace("tarde", time.strftime(" 13:00 ") + " " + time.strftime(" 22:00 "))
    #msg = msg.replace("mañana", time.strftime(" 07:00 ") + " " + time.strftime(" 14:00 "))
    msg = msg.replace("noche", time.strftime(" 22:00 ") + " " + time.strftime(" 05:00 "))
    msg = msg.replace("fiestas", time.strftime(" 04/08/%Y ")+" "+time.strftime(" 09/08/%Y "))
    msg = msg.replace("este mes", time.strftime(" 01/%m/%Y ")+" "+time.strftime(" 30/%m/%Y "))

    return msg

def get_date_rang(message):
    fechas = [time.strftime(" %d/%m/%Y "),time.strftime(" %d/%m/%Y ")]
    num_fechas = 0
    horas = [time.strftime(" %H:%M "),time.strftime(" %H:%M ")]
    num_horas = 0
    msg = message.split()
    for token in msg:
        if token[0].isdigit():
            if token.count("/") > 0:
                fechas[num_fechas] = token
                num_fechas =  num_fechas + 1
            if token.count(":") > 0:
                horas[num_horas] = token
                num_horas =  num_horas + 1

    if num_fechas == 1:
        fechas[1] = fechas[0]
    if num_horas == 1:
        horas[1] = horas[0]

    fechas.extend(horas)
    return fechas


@tb.message_handler(func=lambda msg: get_action(msg.text) == 1, content_types=['text'])
def check_ayuntamiento(message): #Llama a la web del ayuntamiento con lo que sea
    reponses = []

    message.text = process_message(message.text)
    [fecha_desde, fecha_hasta, hora_desde, hora_hasta] = get_date_rang(message.text)

    #fecha_desde = list(map(str, fecha_desde))
    #for i in [0, 1]:
    #    if len(fecha_desde[i]) < 2:
    #        fecha_desde[i] = '0' + fecha_desde[i]

    #fecha_hasta = list(map(str, fecha_hasta))
    #for i in [0, 1]:
    #    if len(fecha_hasta[i]) < 2:
    #        fecha_hasta[i] = '0' + fecha_hasta[i]

    damndata = {'accionWe001': 'ficha',
                'accion': 'calMunicipales',
                'idioma': lng,
                'fechaDesde': fecha_desde, #[0] + '/' + fecha_desde[1] + '/' + fecha_desde[2],
                'fechaHasta': fecha_hasta #[0] + '/' + fecha_hasta[1] + '/' + fecha_hasta[2],
                }

    with requests.session() as s:
        resp = s.get(url_ayu)

        if resp.raise_for_status():  ## DAfuq?? Pero esto hace o no hace?  !!!!!!!!!
            reponse = 'Aiba! ¡Parece que ha habido un problema!'

        resp_post = s.post(url_ayu + '/we001/was/we001Action.do', data=damndata)

        #Arbolizamiento de la página
        tree = html.fromstring(resp_post.content)
        text_lines = tree.xpath('//li[@class ="event-list__item event-list__item--acto"]')
        results = []
        #Recorre las respuestas del event-item-list para sacar lo güeno
        for i, text_line in enumerate(text_lines):
            text_line = text_line.xpath('.//a')[0]
            act_text = text_line.xpath('.//@title')[0]
            end_index = act_text.find("[")
            act_title = act_text[:end_index]
            #Desastre porque no conseguia encontrar ' ' con el estúpido find. (perdoname Ada, porque he pecado)
            if act_text[end_index + 2].isdigit():
                act_data = [act_text[(end_index + 1):(end_index + 3)], act_text[(end_index + 4):-7]]
            else:
                act_data = [act_text[(end_index + 1):(end_index + 2)], act_text[(end_index + 3):-7]]
            act_time = act_text[-6:-1]
            act_info = text_line.xpath('.//@href')[0]

            #A lo loco y con pseudoresaca de programacion (Lo siento, Boris)

            #if not(act_time < hora_desde) and not(act_time > hora_hasta): //CAOS Y DESTRUCCIÖN
            results.append(dict(id=act_title, data= act_data, time=act_time, info=act_info))

    if len(results)==0:
        reponses.append("Aqui pone que no hay nada")
        reponses.append("O has puesto algo mal o Vitoria se ha ido a dormir")
    else:
        if not fecha_desde == fecha_hasta:
            reponses.append("Del "+ fecha_desde + " al " + fecha_hasta + " hay " + str(len(results)) + " eventos.")
        else:
            reponses.append("El " + fecha_desde + " hay " + str(len(results)) + " eventos.")

        if (len(results) < 20):
            for item in results:
                reponses.append(item['id'] + " a las " + item['time'])
        else:
            reponses.append("Ni de coña te los voy a dar todos.")
    #return reponses
    send_naturally(message, reponses)


def get_action(message):
    msg = message.lower()
    msg = ''.join((c for c in unicodedata.normalize('NFD', msg) if unicodedata.category(c) != 'Mn'))
    # reponses = ["Un momentito."] #Todos nuestros operadores estan ocupados. Por favor, espere al final de este episodio de BatleStar gallactica"
    #msg = process_message(message)

    if "que hay" in msg:
        return 1 #reponse = check_ayuntamiento(message)

    if "hola" in msg:
        return 2 #reponses.append("Hola-holita, vecinito!")

    if "kaixo" in msg:
        return 3 #reponse = "aupa, campeon!"

    return 0


def send_naturally(message, reponses):
    tb.send_chat_action(message.chat.id, 'typing')
    #tb.reply_to(message, reponse) #para responder directamente a un mensaje
    for reponse in reponses:
        secs = randint(0, 2)
        time.sleep(secs)
        tb.send_message(message.chat.id, reponse)


tb.polling()
#tb.polling(none_stop=False, interval=10)
