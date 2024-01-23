# coding: utf-8
# ip関連check的ななにか
# (c) kmatsu

'''ip tool的ななにか
* 自分が持っているIPアドレスか
* ipアドレス表記が正しいか
* 宛先に対してデフォルトで使われる送信元IPアドレス

Todo:
    * IPv6対応
'''

import socket
import ipaddress
import psutil
import re


def get_my_nics():
    nic_list = {
        'ipv4': [],
        'ipv6': [],
    }
    def get_nic_addrs(ipv='ipv4'):
        if ipv == 'ipv4':
            family = socket.AF_INET
        elif ipv == 'ipv6':
            family = socket.AF_INET6
        for interface, items in psutil.net_if_addrs().items():
            for nic in items:
                if nic.family == family:
                    yield(interface, nic.address)
    
    return {
        'ipv4': list(get_nic_addrs('ipv4')),
        'ipv6': list(get_nic_addrs('ipv6')),
    }

def is_my_nic_addr(ipaddr):
    """
    自分のIPアドレスかどうか確認
    Args:
        ipaddr (str): ipv4 format
    Return:
        bool : True = is local macine have this ipaddress
    """
    ## この方法だとWindowsしかNICのリストが取れないので、psutil使う方法に変更した。
    # nic_addr_list = socket.gethostbyname_ex(socket.gethostname())
    # check_my_nic_addr = ipaddr in nic_addr_list[2]
    local_nic_list = get_my_nics()
    local_ipv4_list = [nic[1] for nic in local_nic_list['ipv4']]
    check_my_nic_addr = ipaddr in local_ipv4_list
    if check_my_nic_addr:
        return 0
    else:
        return 1

def is_ipv4(ipaddr):
    """
    IPv4表記になっているかを判定
    Args:
        ipaddr (str): ipv4 format
    Return:
        bool : True = is valid ipv4 format
    """
    try:
        # SocketのIPアドレスチェック
        # `socket.inet_aton(ipv4)`
        # だと中途半端なDecimelでもOKになっちゃうのでipaddressを利用
        # 例）1234
        ipaddress.ip_address(ipaddr)
        return True
    except ValueError:
        return False

def is_fqdn(fqdn, strict=False):
    """
    FQDN表記になっているかを判定
    strictはアンダースコアを許可しない
    ラベル（.間）: 63以下
    ドメイン：253以下（.含む）
    文字: a-z, A-Z, 0-9, -, _ (strict=False)
    禁則:
        - 先頭、末尾にハイフン（-）は使えない
        - 先頭、末尾に.ではいけない

    ## 参考: 国際化ドメイン名(IDN; Internationalized Domain Name)
    1つのラベルの長さは15文字以下、UTF-8
    実際には日本語表記のドメインをPunycode変換している。はず。
    Args:
        fqdn (str): hostname or FQDN
        strict (bool): strict チェック
    Return:
        int: 0 is valid fqdn format
    """
    if fqdn[0] == '.' or fqdn[-1] == '.':
        return 1
    elif len(fqdn) > 253:
        return 2

    labels = fqdn.split(".")

    # strict以外はアンダースコアを許可する
    allowed = re.compile(r"(?!-)[a-z0-9-_]{1,63}(?<!-)$", re.IGNORECASE)
    if strict:
        # アンダースコアはNG
        allowed = re.compile(r"(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)
        # 全部数字はNG
        if re.match(r"[0-9]+$", labels[-1]):
            return 3

    check = all(allowed.match(label) for label in labels)
    if not check:
        return 4
    else:
        return 0

def is_fqdn_strict(fqdn):
    """作成中
    より厳密にチェックする。
    ラベル（.間）: 63以下
    ドメイン：253以下（.含む）
    文字: a-z, A-Z, 0-9, -
    禁則:
        - 先頭、末尾にハイフン（-）は使えない
        - 先頭、末尾に.ではいけない

    ## 参考: 国際化ドメイン名(IDN; Internationalized Domain Name)
    1つのラベルの長さは15文字以下、UTF-8
    実際には日本語表記のドメインをPunycode変換している。はず。
    """

def is_resolve(fqdn):
    """
    名前解決が出来るかを判定
    Args:
        fqdn (str): hostname or FQDN
    Return:
        int : 0 is valid, 1 is invalid
    """
    try:
        socket.getaddrinfo (fqdn, None)
        return 0
    except:
        return 1

def resolve(fqdn):
    try:
        socket.getaddrinfo (fqdn, None)
        return 0
    except:
        return 1


def get_my_addrs():
    """
    NICにバインドされているIPアドレスのリストを返す

    Return:
        list : local macine ipaddress list
    """
    nic_addr_list = socket.gethostbyname_ex(socket.gethostname())
    return nic_addr_list

def get_my_default_addr():
    """
    デフォルトルートの送信元IPアドレスを返す
    Return:
        str : defalt route nic ip address
    """
    return socket.gethostbyname(socket.gethostname())

def get_src_addr(dst):
    """get_src_addr
    宛先に対する送信元IPアドレス

    retrun:
        str : 送信元IPアドレス
    """
    # ICMPだと管理者権限必要になるのでUDPに変更
    # sock = socket.socket(
    #     socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect_ex((dst, 0))
    src = sock.getsockname()[0]
    sock.close()

    return src

def is_valid_dst(dst):
    """
    宛先アドレスとして、IPv4表記、FQDN表記、名前解決できるかを返す
    return:
        int: 0: 問題なし
        int: 1: 表記は正しいけど名前解決できない
        int: 2: FQDN, ipv4表記がおかしい
    """

    if not is_fqdn(dst):
        return 2
    
    if not is_resolve(dst):
        return 1
    
    return 0

def is_valid_src(src):
    """
    送信元アドレスとして、IPv4表記、自身のアドレスかを返す
    return:
        int: 0: 問題なし
        int: 1: 自分のIPアドレスじゃない
        int: 2: ipv4表記がおかしい
    """
    return_code = 0
    if not is_ipv4(src):
        return 2
    if not is_my_nic_addr(src):
        return 1
    
    return 0
    