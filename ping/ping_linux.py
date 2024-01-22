import re
from datetime import datetime
from subprocess import run
from shlex import split as shlex_split
from os import environ

# env
my_env = dict(environ)
my_env['LC_ALL'] = 'C'


def ping(dst, src=None, timeout=1, ttl=16, block_size=64, id=255, seq=255):
    """run
    return:
        res(array):  [reply_type, ttl, src, dst, reply_from, starttime, rtt]
                    reply_type is icmp type: 99 is timeout, 98 is unknown (this app specific)
    Todo:
        * 想定外のエラーの場合の処理
        * ログ処理
        * テスト
    """
    starttime = datetime.now()
    icmp_type = 98      # Timeout (Linux Ping not suggest timeout word)
    icmp_code = 0       # default
    reply_from = None

    # ping command generate
    if src:
        ping_cmd = f'ping {dst} -c 1 -W {timeout} -t {ttl} -s {block_size} -I {src}'
    else:
        ping_cmd = f'ping {dst} -c 1 -W {timeout} -t {ttl} -s {block_size}'
    ping_cmd_params = shlex_split(ping_cmd)

    # run ping
    ping_res = run(
        ping_cmd_params,
        capture_output=True,
        text=True,
        env=my_env,
    )

    rtt = (datetime.now() - starttime).total_seconds()
    if ping_res.returncode == 0:
        for i in ping_res.stdout.rstrip("\n").split("\n"):
            ## Success (Get icmp type 0)
            if re.search(r'(?i)\d+ bytes from (\d+\.\d+\.\d+\.\d+): icmp_seq=\d+ ttl=\d+ time=\d+.\d+ ms', i):
                icmp_type = 0
                reply_from = re.search(
                    r'(?i)\d+ bytes from (\d+\.\d+\.\d+\.\d+): icmp_seq=\d+ ttl=\d+ time=\d+.\d+ ms', i
                ).groups()[0]
                break
    else:
        for i in ping_res.stdout.rstrip("\n").split("\n"):
            ## TTL Expire
            if re.search(r'(?i)From (\d+\.\d+\.\d+\.\d+) icmp_seq=\d+ Time to live exceeded', i):
                icmp_type = 11
                reply_from = re.search(
                    r'(?i)From (\d+\.\d+\.\d+\.\d+) icmp_seq=\d+ Time to live exceeded', i
                ).groups()[0]
                break
            ## Unrechable
            elif re.search(r'(?i)Destination (net|host) unreachable', i):
                ## Unrechable
                icmp_type = 3
                icmp_code = 0
                reply_from = re.search(
                    r'(?i)From (\d+\.\d+\.\d+\.\d+)', i
                ).groups()[0]
                break
            ## Transmit Failed
            elif re.search(r"(?i)transmit faile", i):
                icmp_type = 97
                break

    return {
        'starttime': starttime,
        'dst': dst,
        'src': src,
        'type': icmp_type,
        'code': icmp_code,
        'reply_from': reply_from,
        'rtt': rtt,
        'ttl': ttl,
        'id': id,
        'seq': seq
    }

if __name__ == '__main__':
    # import argparse
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('dst', type=str, help='Target Address')
    parser.add_argument('-S', '--src', help='Source Address')
    parser.add_argument('-t', '--timeout', help='Timeout second', default=1)
    parser.add_argument('-H', '--ttl', help='Set the IP TTL field', default=16)
    parser.add_argument('-c', '--count', help='Number of request packets to send', default=1)
    parser.add_argument('-s', '--size', help='Size of ping data to send', default=64)
    args = parser.parse_args()

    from pprint import pprint
    pprint(ping(args.dst, args.src, args.timeout, args.ttl, args.size))
