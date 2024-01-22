from time import sleep, time
from common.iptoolz import get_src_addr
from common.fire_and_forget import fire_and_forget
from os import path, makedirs
from sys import exit as sys_exit

import platform


class MultiPing():
    def __init__(self, base_dir='booya_log', dummy=False):
        self.ping_loop = False
        self.ping_threads = []

        self.ping_list = []
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
    
    def set_target(self, ping_list=[]):
        """
        Args:
            [{dst, src}]: dst addr, src addr
        """
        self.ping_list = []
        self.results = {}

        for pl in ping_list:
            pl.setdefault('src', None)
            dst = str(pl['dst'])
            src = pl['src'] if pl['src'] else get_src_addr(pl['dst'])
            self.ping_list.append({
                'dst': dst,
                'src': src
            })

            self.results[f"{dst}-{src}"] = {'result_history': []}

        return self.ping_list

    @fire_and_forget
    def loop_ping(self, pl, timeout=1, ttl=16, block_size=64):
        while True:
            if self.ping_loop == False:
                sys_exit()

            ping_res = self.ping(pl['dst'], pl['src'], timeout, ttl, block_size)
            self.log_write(ping_res)

            if timeout > ping_res['rtt']:
                sleep(timeout - ping_res['rtt'])

    def start(self):
        self.ping_loop = True

        for pl in self.ping_list:
            th = self.loop_ping(pl)
            self.ping_threads.append(th)

    def stop(self):
        self.ping_loop = False

        # for th in self.ping_threads:
        #     th.join()

        self.ping_threads = []

    def get_ping_list(self):
        """
        Returns:
            [{dst, src}]
        """
        return self.ping_list

    def get_results(self):
        """retun result
        Returns:
            {
                f'{dst}-{src}' : {
                    'starttime': datetime objct,
                    'dst': str dist address,
                    'src': str src address,
                    'type': int icmp type,
                    'code': int icmp code,
                    'reply_from': str reply address,
                    'rtt': float Round Trip time, 
                    'ttl': str ttl,
                    'id': int ping id number,
                    'seq': int ping sequence number,
                    'result': str OK - type 0, NG - other,
                    'result_history': list icmp_type,
                }
            }
        
        Examples:
            {'1.1.1.1-10.156.134.29': 
                [
                    {
                        'starttime': datetime.datetime(2023, 9, 13, 11, 3, 26, 395007),
                        'dst': '1.1.1.1',
                        'src': '10.156.134.29',
                        'type': 0,
                        'code': 0, 
                        'reply_from': '1.1.1.1',
                        'rtt': 2.045834,
                        'ttl': 16,
                        'id': 4725,
                        'seq': 17211,
                        'result': 'OK'
                    },
                ],
            }
        """
        return self.results
    
    def reset_results(self):
        """reset result"""
        self.results = {}
        for pl in self.ping_list:
            self.results[f"{pl['dst']}-{pl['src']}"] = {
                'result_history': []
            }

        return self.results

    def reset(self):
        self.reset_results()

    @fire_and_forget
    def log_write(self, ping_res, postfix='ping', ):
        ## クラス変数更新
        tmp_res_history = self.results[f"{ping_res['dst']}-{ping_res['src']}"]['result_history']
        tmp_res_history.append(ping_res['type'])

        self.results[f"{ping_res['dst']}-{ping_res['src']}"] = {
            'starttime': ping_res['starttime'],
            'dst': ping_res['dst'],
            'src': ping_res['src'],
            'type': ping_res['type'],
            'code': ping_res['code'], 
            'reply_from': ping_res['reply_from'],
            'rtt': ping_res['rtt'],
            'ttl': ping_res['ttl'],
            'id': ping_res['id'],
            'seq': ping_res['seq'],
            'result': 'OK' if ping_res['type'] == 0 else 'NG',
            'result_history': tmp_res_history
        }

        # ファイル出力
        fieldnames = ['starttime', 'result', 'type', 'dst', 'src', 'reply_from', 'rtt',]
        result_file = path.join(self.results_dir, f"{ping_res['dst']}-{ping_res['src']}_{postfix}.csv")

        if not path.isfile(result_file):
            # add header
            with open(result_file, 'w') as f:
                fieldnames.append('\n')
                f.write(','.join(fieldnames))
                # dic_writer = DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                # dic_writer.writeheader()

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
    test_list = [
        {'dst': '1.1.1.1', 'src': None},
        {'dst': '8.8.8.8', 'src': None},
        {'dst': '1.0.0.1', 'src': None},
        {'dst': '10.0.0.1', 'src': None},
    ]
    mp = MultiPing(dummy=True)
    ping_list = mp.set_target(test_list)
    mp.start()

    for i in range(5):
        res = mp.get_results()
        print(res)
        sleep(1)

    mp.stop()
