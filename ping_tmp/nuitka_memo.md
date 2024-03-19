## build by nuitka
### venv
sudo setcap cap_net_raw=eip $(readlink -f $(which python))

### binary
sudo setcap cap_net_raw=eip booya_ping

### Linux Build
python的な環境入れる、多分これで行けると思うけどだめならpyenvのとこ参照
```bash
sudo apt install -y python3 python3-pip python3-venv python-is-python3 \
  ccache patchelf
```
#### pyenv使う場合
nuitka利用する場合はpythonはdisable-sharedしてビルドする必要がある。

前提）ユーザーが'users'グループに所属している事
```bash
git clone https://github.com/pyenv/pyenv.git ${PYENV_ROOT}
```

```bash
sudo apt install -y curl git wget tmux openssl \
  build-essential make ccache patchelf \
  libbz2-dev libffi-dev liblzma-dev \
  libncursesw5-dev libreadline-dev libsqlite3-dev libssl-dev \
  libxml2-dev libxmlsec1-dev llvm tk-dev xz-utils zlib1g-dev

export PYENV_ROOT="/opt/pyenv"
sudo mkdir -p ${PYENV_ROOT}
sudo chgrp -R users ${PYENV_ROOT}
sudo chmod -R g+rwxXs ${PYENV_ROOT}
git clone https://github.com/pyenv/pyenv.git ${PYENV_ROOT}
git clone https://github.com/pyenv/pyenv-virtualenv.git ${PYENV_ROOT}/plugins/pyenv-virtualenv

## python install
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

env PYTHON_CONFIGURE_OPTS="--disable-shared" pyenv install 3.11.6
pyenv rehash
pyenv global 3.11.6

## add bashrc
cat << EOF | tee -a ~/.bashrc > /dev/null
## pyenv
export PYENV_ROOT="/opt/pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:\$PATH"
eval "\$(pyenv init -)"

EOF

## add .profile
cat << 'EOF' | tee -a ~/.profile > /dev/null
## pyenv
export PYENV_ROOT="/opt/pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

EOF

## add .zprofile
cat << 'EOF' | tee -a ~/.zprofile > /dev/null
## pyenv
export PYENV_ROOT="/opt/pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

EOF

## add .zshrc
cat << 'EOF' | tee -a ~/.zshrc > /dev/null
## pyenv
export PYENV_ROOT="/opt/pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

EOF


```


```bash
INSTALL_PATH=${HOME}/.local
BIN_DIR=${HOME}/.local/bin
BOOYA_PATH=${HOME}/tmp/booya_ping

# INSTALL_PATH=/usr/local
# BOOYA_PATH=${HOME}/tmp/booya_ping

cd ${BOOYA_PATH}
git clone https://github.com/hanabi-bro/booya_ping.git .
cd booya_ping
python -m venv venv
source venv/bin/activate
python -m pip install -U pip wheel setuptools cpython
python -m pip install -r requirements_nuitka.txt
python -m nuitka \
  --standalone \
  --follow-imports \
  --assume-yes-for-downloads \
  --enable-console \
  --output-filename=booya_ping \
  --include-package=pygments \
  --include-data-file="./ping/booya_ping.tcss=./" \
  --include-data-file="./ping/config.ini=./" \
  --include-data-file="./README.md=./" \
  --force-stderr-spec="%PROGRAM_BASE%.err.log" \
  --linux-icon="./icon/booya_ping.ico" \
  ./ping/booya_ping.py

cp -r booya_ping_tui.dist ${INSTALL_PATH}/booya_ping
sudo chgrp -R users ${INSTALL_PATH}/booya_ping
sudo chmod -R g+rwxXs ${INSTALL_PATH}/booya_ping
sudo sudo setcap cap_net_raw=eip ${INSTALL_PATH}/booya_ping/booya_ping
ln -fs ${INSTALL_PATH}/booya_ping/booya_ping ${BIN_DIR}/.
```

インストールディレクトリのアップデート
```bash
rsync -rcv --update --exclude=config.ini booya_ping.dist/ ${HOME}/.local/booya_ping
```

## Windows Build
```powershell
python -m nuitka `
  --standalone `
  --follow-imports `
  --assume-yes-for-downloads `
  --enable-console `
  --output-filename=booya_ping `
  --include-package=pygments `
  --include-data-file="./ping/booya_ping.tcss=./" `
  --include-data-file="./ping/config.ini=./" `
  --include-data-file="./README.md=./" `
  --force-stderr-spec="%PROGRAM_BASE%.err.log" `
  --windows-icon-from-ico="./icon/booya_ping.ico" `
  .\ping\booya_ping.py
```



