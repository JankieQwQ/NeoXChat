import json
import threading
import time
import websocket
import ssl

class XChat:
    userset = False
    JOIN_PACKET = {"cmd": "join", "client_key": "neoxchat"}

    def __init__(self, token, channel, nick, password="", headurl="https://xq.kzw.ink/imgs/tx.png"):
        self.channel = channel
        self.nick = nick
        self.password = password
        self.token = token
        self.head_url = headurl
        self.online_users = []
        self.message_function = []
        self.whisper_function = []
        self.join_function = []
        self.leave_function = []
        self.error_function = []
        self.ws = websocket.create_connection("wss://xq.kzw.ink/ws", sslopt={"cert_reqs": ssl.CERT_NONE})
        self.send_packet({**self.JOIN_PACKET, "channel": channel, "nick": nick, "password": password, "token": token})
        threading.Thread(target=self.ping_thread).start()

    def send_message(self, msg, show=False):
        if show:
            self.send_packet({"cmd": "chat", "text": msg, "head": self.head_url, "show": "1"})
        else:
            self.send_packet({"cmd": "chat", "text": msg, "head": self.head_url})

    def send_to(self, target, msg):
        self.send_packet({"cmd": "whisper", "nick": target, "text": msg})

    def move(self, new_channel):
        self.channel = new_channel
        self.send_packet({"cmd": "move", "channel": new_channel})

    def change_nick(self, new_nick):
        self.nick = new_nick
        self.send_packet({"cmd": "changenick", "nick": new_nick})

    def send_packet(self, packet):
        encoded = json.dumps(packet)
        self.ws.send(encoded)

    def daemon(self):
        self.daemon_thread = threading.Thread(target=self.run)
        self.daemon_thread.start()

    def send_image(self, image_url, image_name="Image"):
        self.send_message(f"[![{image_name}]({image_url})]({image_url})")

    def get_image_text(self, image_url, image_name="Image"):
        return f"[![{image_name}]({image_url})]({image_url})"

    def run(self, return_more=False):
        while True:
            try:
                result = json.loads(self.ws.recv())
                cmd = result.get("cmd")
                if cmd == "chat" and result.get("nick") != self.nick:
                    trip = result.get('trip', '')
                    [function(result["text"], result["nick"], trip) if not return_more else function(result) for function in self.message_function]
                elif cmd == "onlineAdd":
                    self.online_users.append(result["nick"])
                    trip = result.get('trip', '')
                    [function(result["nick"], trip) if not return_more else function(result) for function in self.join_function]
                elif cmd == "onlineRemove":
                    self.online_users.remove(result["nick"])
                    [function(result["nick"]) if not return_more else function(result) for function in self.leave_function]
                elif cmd == "onlineSet":
                    self.online_users.extend(result["nicks"])
                elif cmd == "info" and result.get("type") == "whisper":
                    trip = result.get('trip', '')
                    [function(result["msg"], result["from"], trip) if not return_more and "from" in result else function(result) for function in self.whisper_function]
                elif cmd == "warn":
                    if not self.error_function:
                        raise RuntimeError("XChat ERROR:{}".format(result["text"]))
                    else:
                        [function(result["text"]) if not return_more else function(result) for function in self.error_function]
            except json.JSONDecodeError:
                pass

    def ping_thread(self):
        while self.ws.connected:
            self.send_packet({"cmd": "ping"})
            time.sleep(60)
