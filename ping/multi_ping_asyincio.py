from asyncio import new_event_loop, set_event_loop, get_event_loop
from typing import Callable
from time import sleep, time
from common.iptoolz import get_src_addr
from os import path, makedirs
from csv import DictWriter

import platform
# Windows, Linux, Darwin (Mac)
os = platform.system()
if os == 'Windows':
    from ping_win import ping
elif os == 'Linux':
    from ping_linux import ping
elif os == 'Darwin':
    from ping_linux import ping


class MultiPing():
    def __init__(self, ping_list):
        self.ping_loop = False
        self.ping_threads = []
        self.ping_list = ping_list
        self.results = {}

        ## 送信元IPアドレス未指定の場合
        for pl in ping_list:
            if not pl[1]:
                pl[1] = get_src_addr(pl[0])

            self.results[f"{pl[0]}-{pl[1]}"] = []

        ## 結果ディレクトリ
        self.results_dir = path.join(".", "results")
        makedirs(self.results_dir, exist_ok=True)

    def fire_and_forget(func: Callable, *args, **kwargs):
        """ fire and forget decorator """
        def wrapper(*args, **kwargs):
            loop = new_event_loop()
            set_event_loop(loop)
            return loop.run_in_executor(None, func, *args, *kwargs)
        return wrapper

    @fire_and_forget
    def loop_ping(self, dst, src=None, timeout=1, ttl=16, block_size=64):
        while self.ping_loop == True:
            # start_time = time()
            ping_res = ping(dst, src, timeout, ttl, block_size)

            self.log_write(ping_res)

            if timeout > ping_res['rtt']:
                sleep(timeout - ping_res['rtt'])

    def send(self, dst, src=None, timeout=1, ttl=16, block_size=64):
        return ping(dst, src, timeout, ttl, block_size)

    def start(self):
        self.ping_loop = True

        for target in self.ping_list:
            # th = threading.Thread(target=self.loop_ping, args=(target[0], target[1],))
            th = self.loop_ping(target[0], target[1])
            self.ping_threads.append(th)
            # th.start()
            print(target)

    def stop(self):
        self.ping_loop = False

        # for th in self.ping_threads:
        #     th.join()
        loop = get_event_loop()
        loop.stop()

    def get_results(self):
        return self.results

    def log_write(self, ping_res, postfix='ping', ):
        # start_time, end_tiem, dst, src, type, code, reply_from, rtt

        # クラス変数に格納
        self.results[f"{ping_res['dst']}-{ping_res['src']}"].append(ping_res)

        # consoleに表示
        print(ping_res)

        # ファイル出力
        fieldnames = ['starttime', 'result', 'type', 'dst', 'src', 'reply_from', 'rtt',]
        result_file = path.join(self.results_dir, f"{ping_res['dst']}-{ping_res['src']}_{postfix}.csv")

        ping_res['result'] = "OK" if ping_res['type'] == 0 else "NG"

        if not path.isfile(result_file):
            # add header
            with open(result_file, 'a', newline="") as f:
                dic_writer = DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                dic_writer.writeheader()

        with open(result_file, 'a', newline="") as f:
            dic_writer = DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            dic_writer.writerows([ping_res])


if __name__ == '__main__':
    ping_list = [
        ['1.1.1.1', None],
        ['8.8.8.8', None],
        ['1.0.0.1', None],
        ['8.8.4.4', None],
        ['172.16.201.100', None],
        ['172.16.201.254', None],
    ]
    mp = MultiPing(ping_list)
    mp.start()

    for i in range(5):
        print(f'wait: {i}')
        print(mp.get_results())
        sleep(1)

    mp.stop()
    print(mp.get_results())