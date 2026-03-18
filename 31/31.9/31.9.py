import threading
import queue
import random

N = 100
m = 5
t = 100
t1 = 3
iterations = 50

q = queue.Queue()
data = []
results = []
lock = threading.Lock()

def turnstile():
    current_time = -t
    while True:
        try:
            arrival = q.get_nowait()
        except queue.Empty:
            return
        start = max(current_time, arrival)
        service = random.uniform(1, t1)
        finish = start + service
        current_time = finish
        with lock:
            results.append((arrival, finish))

def analyze_data(data, t, parts):
    step = t / parts

    result = [[0] * parts for _ in data]

    for row_i, row in enumerate(data):
        for arrival_time, finish_time in row:
            idx = int((arrival_time + t) / step)

            if idx < 0:
                idx = 0
            if idx >= parts:
                idx = parts - 1

            if finish_time < 0 and result[row_i][idx] == 0:
                result[row_i][idx] = 1

    return [sum(row[i] for row in result) / len(data) for i in range(parts)]

def main():
    for it in range(iterations):
        arrivals = [random.uniform(-t, 0) for _ in range(N)]
        arrivals.sort()

        for a in arrivals:
            q.put(a)

        threads = []
        for _ in range(m):
            th = threading.Thread(target=turnstile)
            th.start()
            threads.append(th)

        for th in threads:
            th.join()

        data.append(results.copy())
        results.clear()
    print(analyze_data(data, t, 20))

if __name__ == "__main__":
    main()