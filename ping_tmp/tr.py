from concurrent.futures import ThreadPoolExecutor
from common.iptoolz import get_src_addr
from random import randint
from time import sleep
from datetime import datetime
from os import makedirs, fsync, replace, remove
from os.path import join, abspath, isfile
from glob import glob
from pickle import load, dump
from tempfile import NamedTemporaryFile

import platform
# Windows, Linux, Darwin (Mac)
os = platform.system()
if os == 'Windows':
    from ping_win import ping
elif os == 'Linux':
    from ping_linux import ping
elif os == 'Darwin':
    from ping_linux import ping

from rich import print, pretty
pretty.install()

class TraceRoute():
    def __init__(self, base_dir='booya_log', delay=0.2, log=True):
        self.delay = delay

        ## 出力ディレクトリ関連
        # self.base_dir = path.join('.', base_dir)
        self.base_dir = base_dir
        ### 結果ディレクトリ
        self.results_dir = join(self.base_dir, "results")
        makedirs(self.results_dir, exist_ok=True)

        ### キャッシュディレクトリ
        self.cache_dir = join(self.base_dir, "cache")
        makedirs(self.cache_dir, exist_ok=True)

    def ping_with_ttl(self, dst, src, timeout=1, ttl=16, block_size=64, id=1, seq=1):
        # 引数でrandintしていても、全部同じになる。import時に計算されてしまうっぽい。
        res = ping(dst, src, timeout=1, ttl=ttl, id=randint(1, 65535), seq=randint(1, 65535))
        return res

    def traceroute(self, dst, src=None,  timeout=1, ttl=10, block_size=64):
        if not src or src is None:
            src = get_src_addr(dst)
        
        routes = []
        routes_verbose = []
        res = []
        with ThreadPoolExecutor(max_workers=ttl) as executor:
            for ttl in range(1, ttl+1):
                try:
                    res.append(
                        executor.submit(self.ping_with_ttl, dst, src, 1, ttl)
                    )
                except:
                    """"""
                sleep(self.delay)
            # executor.mapの場合にDelay入れる方法が分からなかったのでforで回す
            # responses = list(executor.map(lambda ttl: ping_with_ttl(target, ttl, max_hops), range(1, max_hops+1)))

        result = "NG"
        route_num = 0

        for c, r in enumerate(res):
            if result == "NG" and r.result()['type'] == 0:
                if result == "NG":
                    result = 'OK'
            if r.result()['reply_from']:
                routes.append(r.result()['reply_from'])
            else:
                routes.append('*')

            routes_verbose.append(r.result())
            # mapとsubmitでresponsの中身が違う。よく分かってない・・・
            # routes.append(response)      

        tr_res = { 
            'route_num': route_num, 
            'starttime': routes_verbose[0]['starttime'], 
            'dst':       routes_verbose[0]['dst'],
            'src':       routes_verbose[0]['src'],
            'result':    result,
            'routes':    routes,
            'verbose':   routes_verbose,
            'ttl':       ttl,
            'rtt':       (datetime.now() - routes_verbose[0]['starttime']).total_seconds(),
        }

        tr_res['route_num'] = self.get_route_num(tr_res)
        self.log_write(tr_res)
        return tr_res

    def get_route_num(self, tr_res):
        route_name = f'{tr_res["src"]}_{tr_res["dst"]}'
        route_cache = join(self.cache_dir, f"{route_name}")

        # load route history
        if isfile(route_cache):
            with open(route_cache, 'rb') as f:
                route_history = load(f)
        else:
            route_history = []

        route_num = 0
        routes = tr_res['routes']

        # diff route
        try:
            route_num = route_history.index(routes)
        except ValueError as e:
            route_history.append(routes)
            route_num = len(route_history) - 1
        except Exception as e:
            route_num = None
            print(e)

        # if not route_check:
        #     route_history.append(routes)
        #     route_check = 0

        # save route history
        # pickle.dumpが結構壊れるので添付ファイルを作成し、コピーする方式に変更
        # 都度dumpするのではなく、変更があったら書き込む方法に修正したほうがよい
        # それと、DBなどに置き換えも今後の検討
        with NamedTemporaryFile(mode="wb", delete=False) as f:
            dump(route_cache, f)
            # f.flush -> os.fsyncを使い、データが確実にファイルに書き込まれた状態にする
            f.flush()
            fsync(f.fileno())
            tmp_path = f.name

        # 添付ファイルが作成されたら移動(rename)する。
        replace(tmp_path, route_cache)

        with open(route_cache, 'wb') as f:
            dump(route_history, f)

        return route_num

    def clear_route_cache(self, dst='*', src='*'):
        for cache_file in glob(join(self.cache_dir, f'{src}_{dst}')):
            remove(cache_file)

    def log_write(self, tr_res, postfix='traceroute', ):
        # start_time, end_tiem, dst, src, type, code, reply_from, rtt

        # 結果格納
        res_key = f"{tr_res['dst']}-{tr_res['src']}"

        # ファイル出力
        fieldnames = ['starttime', 'dst', 'src', 'result', 'route_num', 'routes']
        result_file = join(self.results_dir, f"{res_key}_{postfix}.csv")

        tmp_res = [
            tr_res['starttime'].strftime('%Y/%m/%d %H:%M:%S.%f'),
            tr_res['dst'],
            tr_res['src'],
            tr_res['result'],
            str(tr_res['route_num']),
            ','.join(tr_res['routes']),
        ]

        if not isfile(result_file):
            # add header
            with open(result_file, 'w', encoding='utf8') as f:
                # print(','.join(fieldnames), file=f)
                f.write(f'{",".join(fieldnames)}\n')

        with open(result_file, 'a', encoding='utf8') as f:
            f.write(f'{",".join(tmp_res)}\n')


if __name__ == "__main__":
    tr = TraceRoute()
    results = tr.traceroute("8.8.8.8", None, 1, 12)
    routes = []

    print(results['route_num'], results['routes'])

