import threading
import queue
import random

N = 100
m = 5
t = 10
t1 = 3
iterations = 100

q = queue.Queue()
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

not_late = [(arrival, finish) for (arrival, finish) in results if finish <= 0.0]

if not_late:
    last_not_late = max(not_late, key=lambda x: x[0])
    arrival_time, finish_time = last_not_late
    print("Last spectator, that was not late, arrived at:", f"{arrival_time:.3f}")
else:
    print("No spectator entered before the match (no one was not late).")