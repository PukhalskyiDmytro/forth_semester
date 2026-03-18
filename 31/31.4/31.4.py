import time
import random
import threading
from collections import deque

t_1 = 0.8
t_2 = 0.9

class PQueue(deque):
    def __init__(self):
        super().__init__()

    def put(self, msg):
        txt, p = msg
        if p == 0:
            super().append(txt)
        else:
            super().appendleft(txt)

    def pop(self):
        return super().pop()

q = PQueue()

def message_generator(max_delay: float):
    while True:
        d = random.uniform(0, max_delay)
        time.sleep(d)

        list_of_words = ["apple", "banana", "orange", "juice"]
        n = len(list_of_words)

        subset_of_indices = bin(random.randint(1, 2**n-1))[2:].zfill(n)
        word = []

        for i in range(n):
            if subset_of_indices[i] == "1":
                word.append(list_of_words[i])

        priority = random.randint(0,1)

        q.put((" ".join(word), priority))

def message_acceptor(max_delay: float):
    while True:
        d = random.uniform(0, max_delay)
        time.sleep(d)

        msg = q.pop()
        print(msg)


def main():
    thread_1 = threading.Thread(target=message_generator, args = (t_1,))
    thread_2 = threading.Thread(target=message_acceptor, args = (t_2,))

    thread_1.start()
    thread_2.start()

    thread_1.join()
    thread_2.join()

if __name__ == "__main__":
    main()