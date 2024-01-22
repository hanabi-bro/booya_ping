from time import sleep, time
from common.iptoolz import get_src_addr
from common.fire_and_forget import fire_and_forget
from os import path, makedirs
from sys import exit as sys_exit

import platform

class Ping():
    def __init__(self, base_dir='booya_log', dummy=False):
        self.results = {}
        ## 出力ディレクトリ関連
        # self.base_dir = path.join('.', base_dir)
        self.base_dir = base_dir
        ### 結果ディレクトリ
        self.results_dir = path.join(self.base_dir, "results")
        makedirs(self.results_dir, exist_ok=True)

        os = platform.system()
        if dummy:
            from ping_dummy import ping
        else:
            if os == 'Windows':
                from ping_win import ping
            elif os == 'Linux':
                from ping_linux import ping
            elif os == 'Darwin':
                from ping_linux import ping
        
        self.ping = ping

    def run(self, dst, src=None,  timeout=1, ttl=128, block_size=64):
        if not src or src is None or src == '':
            src = get_src_addr(dst)

        self.ping_res = self.ping(dst, src, timeout, ttl, block_size)
        self.log_write(self.ping_res)

        return self.ping_res

    @fire_and_forget
    def log_write(self, ping_res, postfix='ping', ):

        # ファイル出力
        fieldnames = ['starttime', 'result', 'type', 'dst', 'src', 'reply_from', 'rtt',]
        result_file = path.join(self.results_dir, f"{ping_res['dst']}-{ping_res['src']}_{postfix}.csv")

        if not path.isfile(result_file):
            # add header
            with open(result_file, 'w') as f:
                fieldnames.append('\n')
                f.write(','.join(fieldnames))

        with open(result_file, 'a') as f:
            f.write(
                ','.join([
                    str(ping_res['starttime']),
                    'OK' if ping_res['type'] == 0 else 'NG',
                    str(ping_res['type']),
                    ping_res['dst'],
                    ping_res['src'],
                    ping_res['reply_from'] if ping_res['reply_from'] else '',
                    str(ping_res['rtt']),
                    '\n'
                ])
            )

if __name__ == '__main__':
    mp = Ping()
    mp.run('1.1.1.1')
    print(mp.ping_res)