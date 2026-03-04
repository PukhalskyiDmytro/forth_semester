import socket
import re

def test_palindrome(string):
    string = re.sub(r'''[ !?.,+:;"'()\-]+''', '', string)
    string = string.lower()
    print(string)
    return string == string[::-1]


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
    pal = str(data, encoding = 'utf-8')
    print(pal)
    res = bytes(test_palindrome(pal)) + b'\n'
    print(res)
    conn.sendall(res)
conn.close()