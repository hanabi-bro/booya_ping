# booya ping
## 概要
* ターミナルでping、traceroute並列実行。
* ターミナルなのでSSH + tmuxやscreenで実行できる。なのでwindowsでもRDPじゃなくていける（SSH有効化が必要）
* キーボードショートカットとマウスクリックの両方で操作可能
  - windowsにsshした場合や、一部windows環境ではマウスが効かない・・・
* ログの自動取得（CSVフォーマット）
  - 指定ディレクトリ下にbooya_logディレクトリを作成し、その下にログを保存
    - ping結果のログ
    - tracerouteのルートログ
    - 初期状態ではユーザディレクトリ配下になる。
* tracerouteは、ルートの切り替わりが分かる

* 補足
  - Tracerouteのルート結果判定は、経路上のルータのping応答性能に依存する。
    
    /// 現時点では1秒以内に応答がないとタイムアウト判定

* 実行ファイル
  - windows
    * booya_ping/booya_ping.exe
  - Linux
    * booya_ping/booya_ping

## 使い方
1. ログディレクトリを指定
    `booya_ping/config.ini`の`base_directory`で出力ディレクトリを指定
    * ユーザディレクトリは'~'で指定可能（Win、Linux共通）
    * ドライブを気にしなければwindowsでもlinuxのPATHフォーマットでもOK

    例）Windowsの場合/opt/log/booya_log
    ```ini
    base_directory = C:\opt\log\booya_log
    ```

    例）linuxの場合~/booya_log
    ★ 権限に注意、ディレクトリ作成の権限がないとエラーで落ちる
    ```ini
    base_directory = ~/booya_log
    ```

2. CLIで'booya_ping'を実行
    config.iniで指定した`booya_log`ディレクトリが自動で作成される。
    
3. `booya_log\conf`配下に宛先リストをcsvで作成
    ```
    ./booya_log/conf/target.csv
    ```
    宛先リストのフォーマットはCSV、ヘッダー無し
    送信元未指定の場合は未記入でOK

    フォーマット
    ```
    宛先1,送信元1
    宛先2,送信元2
    ```
    サンプル（送信元指定なし）
    ```
    8.8.4.4
    1.1.1.1
    ```
    サンプル（送信元指定あり）
    ```
    8.8.4.4,172.16.0.252
    1.1.1.1,172.16.0.252
    ```
4. 「Select」をクリックまたは「T」キーでターゲットを選択
5. ping, traceroutreの実行
   ボタンかショートカットキーでpingやtracerouteを実行、停止。
    `booya_log\results`配下に実行ログが保存される。


## 使い方その２
コマンドオプションで宛先を指定して実行出来るよ

|option|content|
|-|-|
|-p, --ping|pingを実行、引数無し|
|-t, --tr|tracerouteを実行、引数無し|
|-l, --list|宛先リスト、カンマ区切り, 1.1.1.1,8.8.4.4|

例）
```
booya_ping -p -l 1.1.1.1,8.8.4.4
```


## 設置方法
### Windows
任意のディレクトリに配置してパスを通す。
ショートカットを作成して作業フォルダーを空にしておけば、ショートカットからの起動もできる。と思う。

#### サンプル

* 配置先：'c:\opt\appz\booya_ping'
  - current user
    ```powershell
    $new_path = [Environment]::GetEnvironmentVariable("Path", "User")
    $new_path += ';c:\opt\appz\booya_ping'
    [Environment]::SetEnvironmentVariable("Path", $new_path, "User")
    ```
  - system global
    ```powershell
    $new_path = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $new_path += ';c:\opt\appz\booya_ping'
    [Environment]::SetEnvironmentVariable("Path", $new_path, "Machine")
    ```
  - 削除（たぶんできそう）
    ```powershell
    Set-Item ENV:Path $ENV:Path.Replace("c:\opt\appz\booya_ping", "")
    ```
  - 変更
    ```powershell
    Set-Item ENV:Path $ENV:Path.Replace("置換前のパス;", "置換後のパス;")
    ```

### linux
任意のディレクトリに解凍して、booya_pingのsymlinkをパスが通ってるところに作成すればOK
#### サンプル
* 配置先：'/usr/local/booya_ping'
* bin dir：'/usr/local/bin'

##### Debian, Ubuntu
```bash
INSTALL_DIR=/usr/local
BIN_DIR=/usr/local/bin
cd ~

## Debian, Ubuntu
sudo tar xf booya_ping_linux.tgz -C $INSTALL_DIR/.

sudo chgrp -R users ${INSTALL_DIR}/booya_ping
sudo chmod -R g+rwxXs ${INSTALL_DIR}/booya_ping
sudo ln -fs ${INSTALL_DIR}/booya_ping/booya_ping ${BIN_DIR}/.

## Start up
booya_ping
```
##### RaspberryPi
```bash
INSTALL_DIR=/usr/local
BIN_DIR=/usr/local/bin
cd ~

## Raspberrypi
sudo tar xf booya_ping_raspberrypi.tgz -C $INSTALL_DIR/.

sudo chgrp -R users ${INSTALL_DIR}/booya_ping
sudo chmod -R g+rwxXs ${INSTALL_DIR}/booya_ping
sudo ln -fs ${INSTALL_DIR}/booya_ping/booya_ping ${BIN_DIR}/.

## Start up
booya_ping
```

##### 補足
permitエラーが出た場合は以下試してみて
```bash
sudo setcap cap_net_raw=eip ${INSTALL_DIR}/booya_ping/booya_ping
```
