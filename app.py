from flask import Flask           #建立網站伺服器 使用 Flask 模組
from flask import request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import requests, os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET 

app = Flask(__name__)

#Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
#Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

#建立callback路由的程式碼, 檢查LINE Bot的資料是否正確
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'
    
#如果接到使用者傳送的訊息, 就將相對應的文字訊息傳回
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    mtext = event.message.text          #取得使用者傳送的文字於mtext變數中
    str1 = prizeNum(1) + '\n\n' + prizeNum(2)

    if (mtext == '@本期中獎號碼'):      #顯示本期中獎號碼(前置@與一般輸入文字區別)
        try:                            #依選單指令回傳文字訊息
            message = TextSendMessage(text = prizeNum(0))
            line_bot_api.reply_message(event.reply_token,message) 
        except:                         #錯誤時回傳「發生錯誤」訊息
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤!'))           

    elif (mtext == '@前期中獎號碼'):
        try:
            message =TextSendMessage(text = str1)
            line_bot_api.reply_message(event.reply_token,message)
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤!'))        

    elif (mtext == '@後三碼對獎'):
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='請輸入發票最後三碼：'))

    elif (len(mtext) == 3 and mtext.isdigit()):  #判斷是否中獎    
        try:
            content = requests.get('https://invoice.etax.nat.gov.tw/invoice.xml')
            tree = ET.fromstring(content.text)
            items = list(tree.iter(tag='item'))  #取得item標籤內容
            title = items[0][0].text             #期別
            ptext = items[0][3].text             #本期中獎號碼
            ptext = ptext.replace('<p>','').replace('</p>','')
            temlist = ptext.split('：')      
            prizelist = []                       #特別獎或特獎後三碼
            prizelist.append(temlist[1][5:8])
            prizelist.append(temlist[2][5:8])
            tem = temlist[3].split('、')
            prize6list1 = []                     #頭獎後三碼六獎中獎號碼
            for i in range(3):
                prize6list1.append(tem[i][5:8])
                if len(temlist) > 4:
                    prize6list2 = temlist[4].split('、')  #增開六獎
                else:
                    prize6list2 = []
            if mtext in prizelist:
                message = '對中特別獎或特獎後三碼，好緊張！\n'
                message += prizeNum(0)
                message = message[:53]                    #移除頭獎
            elif mtext in prize6list1:
                message = '至少中200元，再對 頭獎 前五碼！\n'
                str2 = prizeNum(0)
                message = message + title + str2[36:]     #移除特獎  
            elif mtext in prize6list2:
                message = '這張發票中200元。'
            else:
                message = '這張槓龜，輸入下一張。'
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=message))
        except:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發票號碼讀取錯誤！'))
    else:
          line_bot_api.reply_message(event.reply_token,TextSendMessage(text='請輸入發票後三碼或按選單。'))

def prizeNum(n):
    content=requests.get('https://invoice.etax.nat.gov.tw/invoice.xml')           
    tree = ET.fromstring(content.text)   #解析XML
    items = list(tree.iter(tag='item'))  #取得item標籤內容
    title = items[n][0].text             #期別
    ptext = items[n][3].text             #中獎號碼
    ptext = ptext.replace('<p>','').replace('</p>','\n')
    return title + '\n' + ptext[:-1]     #ptext[:-1]為移除最後一個\n
        
if __name__ == '__main__':
    app.run()
