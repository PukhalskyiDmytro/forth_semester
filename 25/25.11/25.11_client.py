import socket

HOST = 'localhost'
PORT = 20002

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

while True:
    to_send = input('?: ')
    if not to_send:
        break
    s.sendall(to_send.encode('utf-8'))
    print('sent')
    data = s.recv(1024)
    if not data:
        break
    text = data.decode('utf-8').strip()
    print('received')
    print(text)

s.close()
