#! /usr/bin/python3

from aiohttp import ClientSession, TCPConnector, ClientTimeout
import asyncio, itertools, random, requests, sys, threading, time

vote_endpoint = "http://34.117.144.244:80/castVote"

db_ip = "http://34.66.242.58:80"

election_data_fetch = {
    "operation": "SELECT",
    "columns": "*",
    "tablename": "votingperiod",
    "where": ["1=1"]
}

election_data = requests.post(db_ip + "/api/db/read", json=election_data_fetch)
election_data_string = election_data.text.replace(" ", "").replace("\n", "")
indices = [i for i, x in enumerate(election_data_string) if x == "]"]
indices.pop()
indices.insert(0, 0)
election_data_list = [election_data_string[indices[i]: indices[i + 1]] for i in range(len(indices) - 1)]
for i in range(len(election_data_list)):
    election_data_list[i] = election_data_list[i].replace("[", "").replace("]", "").strip(",")
final_election_data_list = []
for i in election_data_list:
    temp = i.split(",")
    for j in range(len(temp)):
        temp[j] = temp[j].replace('"', "")
    final_election_data_list.append(temp)

class Counter(object):
    __slots__ = (
        "value",
        "_step",
    )

    def __init__(self, init=0, step=1):
        self.value = init
        self._step = step

    def increment(self, num_steps=1):
        self.value += self._step * num_steps

class FastCounter(Counter):
    __slots__ = (
        "_number_of_read",
        "_counter",
        "_lock",
        "_step",
    )

    def __init__(self, init=0, step=1):
        self._number_of_read = 0
        self._step = step
        self._counter = itertools.count(init, step)
        self._lock = threading.Lock()

    def increment(self, num_steps=1):
        for i in range(0, num_steps):
            next(self._counter)

    @property
    def value(self):
        with self._lock:
            value = next(self._counter) - self._number_of_read
            self._number_of_read += self._step
        
        return value

data = {
    "level_number": 0,
    "cluster_id": 1
}

async def send_request(session, batch_id):
    data["batch_id"] = batch_id
    
    for j in range(len(final_election_data_list)):
        temp = "{}::{}".format(final_election_data_list[j][0], final_election_data_list[j][2])
        
        data[temp] = 0
    
    x = random.randint(0, len(final_election_data_list) - 1)
    lucky_candidate = final_election_data_list[x][2]
    lucky_party = final_election_data_list[x][0]
    
    data["{}::{}".format(lucky_party, lucky_candidate)] = 1
    
    async with session.post(vote_endpoint, json=data, timeout=ClientTimeout(total=20*60)) as resp:
        if resp.status != 200:
            failure_ctr.increment()
            print(resp.status, batch_id)
        
        if resp.status == 200:
            success_ctr.increment()

        return await resp.read()

async def bound_request(sem, session, batch_id):
    async with sem:
        await send_request(session, batch_id)

limit = 100
total = 20_000

success_ctr = FastCounter()
failure_ctr = FastCounter()

async def start_requests():
    # async with ClientSession(connector=TCPConnector(limit=limit, limit_per_host=limit), timeout=ClientTimeout(total=(2*60*60))) as session:
    async with ClientSession(timeout=ClientTimeout(total=None, connect=None, sock_connect=None, sock_read=None)) as session:
        # tasks = list()

        sem = asyncio.Semaphore(limit)

        # tasks = [asyncio.ensure_future(bound_request(sem, session, num)) for num in range(1, total + 1)]
        tasks = [asyncio.create_task(bound_request(sem, session, num)) for num in range(1, total + 1)]

        # for num in range(1, total + 1):
        #     task = asyncio.ensure_future(bound_request(sem, session, num))
        #     tasks.append(task)
        
        await asyncio.gather(tasks)
    return

loop = asyncio.get_event_loop()

try:
    start_time = time.time()

    loop.run_until_complete(asyncio.ensure_future(start_requests()))
    loop.close()

    end_time = time.time()
    print("\n\n\tExecution time {} seconds".format(end_time - start_time))

    print("\n\tSuccessful requests sent = {}".format(success_ctr.value))
    print("\n\tUnSuccessful requests sent = {}".format(failure_ctr.value))

    print("\n\n\tMetrics")
    print("\n\tRequests/second = {}".format(success_ctr.value / (end_time - start_time)))

    sys.exit(0)

except KeyboardInterrupt:
    loop.close()

    sys.exit(1)
