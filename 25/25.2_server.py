import socket

def calculate(string):
    return eval(string)

HOST = ''
PORT = 20002

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print('Connected by', addr)
while True:
    data = conn.recv(1024)
    if not data: break
    expr = data.decode('utf-8').strip()
    print("received: ", expr)
    conn.sendall(str(calculate(expr)).encode('utf-8'))
conn.close()