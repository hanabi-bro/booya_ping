import common.iptoolz as itz
from common.log import my_logger

logger = my_logger(__name__)

def addr_validate_target(dst, src):
    """"""
    # 1. target addr not valid format
    # 2. target hostname not resolve
    # 3. src addr not valid format
    # 4. src addr not in local pc
    # 5. src hostname not resolve
    
    # validate target addr is valid format

    validate_err = {'err': [], 'warn': []}
    validate_err = addr_validate_dst(dst, validate_err)
    validate_err = addr_validate_src(dst, validate_err)


    return validate_err

def addr_validate_dst(dst, validate_err):
    validate_err.setdefault('err', [])
    validate_err.setdefault('warn', [])
    if itz.is_fqdn(dst) != 0:
        validate_err['err'].append(f'dst addr {dst} is not valid format')
    elif itz.is_resolve(dst) != 0:
        validate_err['err'].append(f'dst addr {dst} can not resolved name')

    return validate_err

def addr_validate_src(src, validate_err):
    validate_err.setdefault('err', [])
    validate_err.setdefault('warn', [])
    if itz.is_fqdn(src) != 0:
        validate_err['err'].append(f'dst addr {src} is not valid format')
    elif itz.is_resolve(src) != 0:
        validate_err['err'].append(f'src addr {src} can not resolved name')
    elif itz.is_my_nic_addr(src) != 0:
        validate_err['warn'].append(f'src addr {src} is not in local nic')

    return validate_err
