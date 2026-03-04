import socket

HOST = 'localhost'
PORT = 20002

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
while True:
    to_send = input('?: ')
    if not to_send: break
    s.sendall(bytes(to_send, encoding='utf-8'))
    print('sent')
    data = s.recv(1024)
    print('received')
    b = bool(data[:-1])
    if b:
        print(to_send, ' - pal')
    else:
        print(to_send, ' - not pal')
s.close()
