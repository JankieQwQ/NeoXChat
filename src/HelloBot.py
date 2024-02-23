import XChat
import time

def message_got(message,sender,trip):
    if message == "Hello":
        chat.send_message('Hello!')

chat = XChat.XChat(token,"xq102210","HelloBot","hello")
chat.message_function += [message_got]
xc.run(False)
