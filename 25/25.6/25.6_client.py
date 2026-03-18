import socket

HOST = 'localhost'
PORT = 20002

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
while True:
    to_send = input('info to save: ')
    if not to_send: break
    s.sendall(to_send.encode('utf-8'))
    print('sent')
    data = s.recv(1024)
    print('received')
    b = bool(data[:-1])
    print("Information was saved successfully" if b else "Error")
s.close()
