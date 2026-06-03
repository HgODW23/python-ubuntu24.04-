# 网络调试工具

中文说明见上半部分，English documentation is available in the second half.

这是一个基于 Python Tkinter 的图形化网络调试工具，用于快速测试 TCP Client、TCP Server 和 UDP 收发。工具支持文本/HEX 发送、HEX 接收显示、常用编码切换、自动追加 `\r\n`、目标地址历史记录，以及 Windows 单文件 exe 打包。

## 文件说明

```text
.
├── net_debug_tool.py       # 主程序，Tkinter GUI 网络调试工具
└── build_windows_exe.bat   # Windows 下使用 PyInstaller 打包 exe
```

## 功能特性

- 支持 `tcp_client`、`tcp_server`、`udp` 三种模式。
- 支持 `gbk`、`gb2312`、`utf-8`、`latin1` 编码。
- 支持发送 HEX 数据，例如 `01 03 00 00 00 02`。
- 支持接收区按 HEX 显示。
- 支持发送时自动追加 `\r\n`。
- 自动保存上次使用的模式、地址、端口、编码和开关状态。
- 记录最近使用过的 Host 和 Port，方便重复调试。
- 支持 `Enter` 发送，`Shift + Enter` 换行。

配置文件会保存到用户目录：

```text
~/.net_debug_tool.json
```

## 运行环境

需要 Python 3。Tkinter 通常随 Python 自带。

Linux 如果缺少 Tkinter，可安装系统包：

```bash
sudo apt install python3-tk
```

Windows 请安装 Python 3，并在安装时勾选：

```text
Add python.exe to PATH
```

## 启动工具

在当前目录执行：

```bash
python3 net_debug_tool.py
```

Windows 下也可以执行：

```bat
python net_debug_tool.py
```

启动后窗口标题为 `Network Debug Tool`。

## 界面字段说明

| 字段 | 说明 |
| --- | --- |
| Mode | 工作模式：`tcp_client`、`tcp_server`、`udp` |
| Host | 目标主机或本地绑定地址 |
| Port | 目标端口或本地监听端口 |
| Encoding | 文本发送/接收使用的编码 |
| Send HEX | 勾选后发送框按 HEX 字符串解析 |
| Recv HEX | 勾选后接收区按 HEX 格式显示数据 |
| Auto `\r\n` | 发送前自动追加回车换行 |
| Connect/Start | 连接远端或启动监听 |
| Disconnect/Stop | 断开连接或停止监听 |
| Send | 发送输入框中的内容 |
| Clear Log | 清空接收/日志窗口 |

## TCP Client 模式

用于连接远端 TCP Server。

示例：

```text
Mode: tcp_client
Host: 192.168.1.100
Port: 5000
```

操作步骤：

1. 选择 `tcp_client`。
2. 填写远端服务器 IP 和端口。
3. 点击 `Connect/Start`。
4. 在 Send 区输入数据。
5. 点击 `Send` 或按 `Enter` 发送。

## TCP Server 模式

用于在本机监听 TCP 端口，等待客户端连接。

示例：

```text
Mode: tcp_server
Host: 0.0.0.0
Port: 5000
```

说明：

- `Host` 填 `0.0.0.0` 表示监听本机所有网卡。
- 也可以填指定本机 IP，例如 `192.168.1.10`。
- 当前程序同一时间保存一个客户端连接；新的客户端接入时会替换旧连接。

## UDP 模式

UDP 模式会先绑定本地地址和端口，同时也用 Host/Port 作为默认发送目标。

示例：

```text
Mode: udp
Host: 0.0.0.0
Port: 5000
```

UDP 发送规则：

- 如果已经收到过 UDP 数据，会优先回复最后一个发送方。
- 如果还没有收到过 UDP 数据，会发送到界面中填写的 Host/Port。

如果需要主动发往某个设备，可将 Host 填为目标 IP，Port 填为目标端口，然后点击 `Connect/Start` 后发送。

## HEX 收发

### 发送 HEX

勾选 `Send HEX` 后，发送框内容会按十六进制字节解析：

```text
01 03 00 00 00 02
```

程序会自动忽略空格和换行，但 HEX 字符数量必须是偶数。

### 接收 HEX

勾选 `Recv HEX` 后，接收区会把数据按十六进制显示：

```text
RX (gbk, 6 bytes): 01 03 00 00 00 02
```

## 快捷键

| 快捷键 | 作用 |
| --- | --- |
| Enter | 发送 Send 区当前内容 |
| Shift + Enter | 在 Send 区插入换行 |
| Ctrl + A | 全选当前输入框或文本框内容 |

## Windows 打包 exe

在 Windows 下双击或命令行运行：

```bat
build_windows_exe.bat
```

脚本会自动执行：

```bat
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name NetDebugTool net_debug_tool.py
```

打包完成后生成：

```text
dist\NetDebugTool.exe
```

如果提示找不到 Python，请先安装 Python 3，并确认 `python` 已加入 PATH。

## 常见问题

### 端口绑定失败

可能原因：

- 端口已经被其他程序占用。
- Linux 下绑定低端口需要权限。
- TCP Server/UDP 的 Host 填写了非本机 IP。

可尝试：

```text
Host: 0.0.0.0
Port: 5000
```

或换一个端口。

### 收到中文乱码

切换 Encoding。常见设备使用 `gbk` 或 `gb2312`，现代服务通常使用 `utf-8`。

### HEX 发送失败

确认勾选 `Send HEX` 后输入的是合法十六进制字符，并且字符数量为偶数。

正确示例：

```text
AA 55 01 02 0D 0A
```

错误示例：

```text
AA 5
```

### TCP Server 无法发送

TCP Server 模式必须先有客户端连接。日志中出现 `Client connected` 后才能向客户端发送数据。

### UDP 发送目标不对

UDP 模式收到数据后会自动把发送目标更新为最后一个发送方。如果要主动发给指定目标，请先确认 Host/Port 填写正确，并在未收到其他 UDP 数据前发送。

---

# Network Debug Tool

This is a Python Tkinter based GUI network debugging tool for quickly testing TCP Client, TCP Server, and UDP communication. It supports text/HEX sending, HEX receive display, selectable encodings, automatic `\r\n` appending, target history, and Windows single-file exe packaging.

## Files

```text
.
├── net_debug_tool.py       # Main Tkinter GUI application
└── build_windows_exe.bat   # Windows PyInstaller packaging script
```

## Features

- Supports `tcp_client`, `tcp_server`, and `udp` modes.
- Supports `gbk`, `gb2312`, `utf-8`, and `latin1` encodings.
- Sends HEX data, for example `01 03 00 00 00 02`.
- Displays received data as HEX.
- Appends `\r\n` automatically before sending when enabled.
- Saves the last used mode, host, port, encoding, and options.
- Keeps recent Host and Port history for repeated debugging.
- Supports `Enter` to send and `Shift + Enter` to insert a newline.

The configuration file is saved in the user home directory:

```text
~/.net_debug_tool.json
```

## Requirements

Python 3 is required. Tkinter is usually included with Python.

On Linux, install Tkinter if it is missing:

```bash
sudo apt install python3-tk
```

On Windows, install Python 3 and make sure this option is selected during installation:

```text
Add python.exe to PATH
```

## Run

Run from this directory:

```bash
python3 net_debug_tool.py
```

On Windows:

```bat
python net_debug_tool.py
```

The application window title is `Network Debug Tool`.

## UI Fields

| Field | Description |
| --- | --- |
| Mode | Work mode: `tcp_client`, `tcp_server`, or `udp` |
| Host | Remote target host or local bind address |
| Port | Remote target port or local listening port |
| Encoding | Encoding used for text send/receive |
| Send HEX | Parse the send box content as HEX bytes |
| Recv HEX | Display received data in HEX format |
| Auto `\r\n` | Append carriage return and newline before sending |
| Connect/Start | Connect to remote target or start listening |
| Disconnect/Stop | Disconnect or stop listening |
| Send | Send the content in the Send box |
| Clear Log | Clear the receive/log window |

## TCP Client Mode

Use this mode to connect to a remote TCP Server.

Example:

```text
Mode: tcp_client
Host: 192.168.1.100
Port: 5000
```

Steps:

1. Select `tcp_client`.
2. Enter the remote server IP and port.
3. Click `Connect/Start`.
4. Enter data in the Send area.
5. Click `Send` or press `Enter`.

## TCP Server Mode

Use this mode to listen on a local TCP port and wait for a client connection.

Example:

```text
Mode: tcp_server
Host: 0.0.0.0
Port: 5000
```

Notes:

- `0.0.0.0` listens on all local network interfaces.
- You can also bind to a specific local IP, for example `192.168.1.10`.
- The program keeps one active client connection at a time. A new client replaces the old connection.

## UDP Mode

UDP mode binds to a local address and port. The same Host/Port is also used as the default send target.

Example:

```text
Mode: udp
Host: 0.0.0.0
Port: 5000
```

UDP sending behavior:

- If UDP data has already been received, replies are sent to the last sender.
- If no UDP data has been received yet, data is sent to the Host/Port shown in the UI.

To actively send data to a device, set Host to the target IP and Port to the target port, then click `Connect/Start` and send data.

## HEX Send And Receive

### Send HEX

When `Send HEX` is enabled, the Send box is parsed as hexadecimal bytes:

```text
01 03 00 00 00 02
```

Spaces and newlines are ignored, but the number of HEX characters must be even.

### Receive HEX

When `Recv HEX` is enabled, received data is displayed as hexadecimal bytes:

```text
RX (gbk, 6 bytes): 01 03 00 00 00 02
```

## Shortcuts

| Shortcut | Action |
| --- | --- |
| Enter | Send current Send box content |
| Shift + Enter | Insert a newline in the Send box |
| Ctrl + A | Select all content in the current input or text box |

## Build Windows EXE

On Windows, run:

```bat
build_windows_exe.bat
```

The script runs:

```bat
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name NetDebugTool net_debug_tool.py
```

The generated executable is:

```text
dist\NetDebugTool.exe
```

If Python is not found, install Python 3 first and make sure `python` is available in PATH.

## FAQ

### Port bind failed

Possible causes:

- The port is already used by another program.
- Binding a low port on Linux requires permission.
- TCP Server or UDP Host is set to an IP that does not belong to this machine.

Try:

```text
Host: 0.0.0.0
Port: 5000
```

Or use another port.

### Chinese text is garbled

Switch Encoding. Many devices use `gbk` or `gb2312`; modern services often use `utf-8`.

### HEX sending failed

Make sure `Send HEX` is enabled and the input contains valid hexadecimal characters with an even length.

Correct example:

```text
AA 55 01 02 0D 0A
```

Incorrect example:

```text
AA 5
```

### TCP Server cannot send data

TCP Server mode requires a connected client. You can send data after the log shows `Client connected`.

### UDP sends to the wrong target

After receiving UDP data, the tool automatically sends replies to the last sender. To actively send to a specific target, make sure Host/Port are set correctly and send before receiving data from another sender.
