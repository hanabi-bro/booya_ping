from time import sleep
from common.iptoolz import get_src_addr
from common.fire_and_forget import fire_and_forget
from os import path, makedirs
from sys import exit as sys_exit

from tr import TraceRoute


class MultiTraceroute():
    def __init__(self, base_dir='booya_log'):
        self.tr = TraceRoute(base_dir)
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

        ### キャッシュディレクトリ
        self.cache_dir = path.join(self.base_dir, "cache")
        makedirs(self.cache_dir, exist_ok=True)

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

            self.results[f"{dst}-{src}"] = {
                'starttime': '',
                'dst': pl['dst'],
                'src': pl['src'],
                'result': '',
                'rtt': '',
                'ttl': '',
                'route_num': '',
                'route_history': [],
                'result_history': [],
                'routes': [],
            }
        
        return self.ping_list

    @fire_and_forget
    def loop_ping(self, dst, src, timeout=3, ttl=16, block_size=64):
        while True:
            if self.ping_loop == False:
                sys_exit()

            ping_res = self.tr.traceroute(dst, src, timeout, ttl, block_size)
            self.log_write(ping_res)

            if timeout > ping_res['rtt']:
                sleep(timeout - ping_res['rtt'])

    def start(self):
        self.ping_loop = True

        for target in self.ping_list:
            th = self.loop_ping(target['dst'], target['src'])
            self.ping_threads.append(th)

    def stop(self):
        self.ping_loop = False

        for th in self.ping_threads:
            th.join()

        self.ping_threads = []

    def get_ping_list(self):
        """
        Returns:
            [{dst, src}]
        """
        return self.ping_list

    def get_results(self):
        """
        Returns:
            {
                self.results[f"{dst}-{src}"]: {
                    'starttime': '',
                    'dst': pl[0],
                    'src': pl[1],
                    'result': '',
                    'rtt': '',
                    'ttl': '',
                    'route_num': '',
                    'route_history': [],
                    'result_history': [],
                    'routes': [],
                }            
            }

        """
        return self.results

    def reset_results(self):
        """reset result"""
        self.results = {}
        for pl in self.ping_list:
            self.results[f"{pl['dst']}-{pl['src']}"] = {
                'starttime': '',
                'dst': pl['dst'],
                'src': pl['src'],
                'result': '',
                'rtt': '',
                'ttl': '',
                'route_num': '',
                'route_history': [],
                'result_history': [],
                'routes': [],
            }

        return self.results

    def log_write(self, ping_res, postfix='traceroute', ):
        # start_time, end_tiem, dst, src, type, code, reply_from, rtt

        # 結果格納
        res_key = f"{ping_res['dst']}-{ping_res['src']}"

        self.results[res_key]['starttime'] = ping_res['starttime']
        self.results[res_key]['rtt'] = ping_res['rtt']
        self.results[res_key]['ttl'] = ping_res['ttl']
        self.results[res_key]['route_num'] = ping_res['route_num']
        self.results[res_key]['route_history'].append(ping_res['route_num'])
        self.results[res_key]['result_history'].append(ping_res['result'])
        self.results[res_key]['routes'] = ping_res['routes']

        # ファイル出力
        fieldnames = ['starttime', 'dst', 'src', 'result', 'route_num', 'routes']
        result_file = path.join(self.results_dir, f"{ping_res['dst']}-{ping_res['src']}_{postfix}.csv")

        tmp_res = [
            ping_res['starttime'].strftime('%Y/%m/%d %H:%M:%S.%f'),
            ping_res['dst'],
            ping_res['src'],
            ping_res['result'],
            str(ping_res['route_num']),
            ','.join(ping_res['routes']),
        ]

        if not path.isfile(result_file):
            # add header
            with open(result_file, 'w', encoding='utf8') as f:
                # print(','.join(fieldnames), file=f)
                f.write(f'{",".join(fieldnames)}\n')

        with open(result_file, 'a', encoding='utf8') as f:
            f.write(f'{",".join(tmp_res)}\n')

    def delete_route_cache(self, src='*', dst='*'):
        self.tr.clear_route_cache(src, dst)


if __name__ == '__main__':
    test_list = [
        {'dst': '1.1.1.1', 'src': None},
        {'dst': '8.8.8.8', 'src': None},
        {'dst': '1.0.0.1', 'src': None},
        {'dst': '10.0.0.1', 'src': None},
    ]
    mtr = MultiTraceroute()
    ping_list = mtr.set_target(test_list)
    mtr.start()

    for i in range(10):
        res = mtr.get_results()
        print(res)
        sleep(1)

    mtr.stop()
    mtr.delete_route_cache()
