import socket

def save_file(string):
    try:
        path = "C:/Users/Dmytro/PycharmProjects/College/data.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(string)

        print("Saved successfully")
        return True
    except OSError as e:
        print("Save failed:", e)
        return False

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
    pal = data.decode('utf-8').strip()
    print(pal)
    res = bytes(save_file(pal)) + b'\n'
    print(res)
    conn.sendall(res)
conn.close()