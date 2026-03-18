import socket

HOST = ''
PORT = 20002

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(2)

print('Waiting for client 1...')
conn1, addr1 = s.accept()
print('Client 1 connected:', addr1)

print('Waiting for client 2...')
conn2, addr2 = s.accept()
print('Client 2 connected:', addr2)

while True:
    data1 = conn1.recv(1024)
    if not data1:
        break
    text1 = data1.decode('utf-8').strip()
    print('received from client 1:', text1)
    conn2.sendall(('Client 1: ' + text1).encode('utf-8'))

    data2 = conn2.recv(1024)
    if not data2:
        break
    text2 = data2.decode('utf-8').strip()
    print('received from client 2:', text2)
    conn1.sendall(('Client 2: ' + text2).encode('utf-8'))

conn1.close()
conn2.close()
s.close()