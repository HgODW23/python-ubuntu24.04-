#!/usr/bin/env python3
import json
import os
import queue
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk


CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".net_debug_tool.json")
DEFAULT_CONFIG = {
    "mode": "tcp_client",
    "host": "127.0.0.1",
    "port": "5000",
    "host_history": ["127.0.0.1"],
    "port_history": ["5000"],
    "encoding": "gbk",
    "send_hex": False,
    "recv_hex": False,
    "auto_newline": False,
}


class NetDebugTool:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Network Debug Tool")
        self.root.geometry("980x640")

        config = self._load_config()
        self.mode = tk.StringVar(value=config["mode"])
        self.host = tk.StringVar(value=config["host"])
        self.port = tk.StringVar(value=config["port"])
        self.host_history = self._normalize_history(config.get("host_history"), config["host"])
        self.port_history = self._normalize_history(config.get("port_history"), config["port"])
        self.encoding = tk.StringVar(value=config["encoding"])

        self.send_hex = tk.BooleanVar(value=config["send_hex"])
        self.recv_hex = tk.BooleanVar(value=config["recv_hex"])
        self.auto_newline = tk.BooleanVar(value=config["auto_newline"])

        self.connected = False
        self.running = False

        self.sock = None
        self.server_sock = None
        self.client_sock = None
        self.client_addr = None

        self.recv_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.recv_thread = None
        self.accept_thread = None

        self._build_ui()
        self.root.after(100, self._drain_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _load_config(self):
        config = DEFAULT_CONFIG.copy()
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                for key in config:
                    if key in saved:
                        config[key] = saved[key]
        except FileNotFoundError:
            pass
        except Exception:
            pass
        return config

    def _normalize_history(self, values, current):
        history = []
        for value in values or []:
            text = str(value).strip()
            if text and text not in history:
                history.append(text)
        current = str(current).strip()
        if current and current not in history:
            history.insert(0, current)
        return history[:20]

    def _remember_current_target(self):
        host = self.host.get().strip()
        port = self.port.get().strip()
        if host:
            self.host_history = self._normalize_history([host] + self.host_history, host)
            self.host_box.configure(values=self.host_history)
        if port:
            self.port_history = self._normalize_history([port] + self.port_history, port)
            self.port_box.configure(values=self.port_history)

    def _save_config(self):
        self._remember_current_target()
        config = {
            "mode": self.mode.get(),
            "host": self.host.get().strip(),
            "port": self.port.get().strip(),
            "host_history": self.host_history,
            "port_history": self.port_history,
            "encoding": self.encoding.get(),
            "send_hex": self.send_hex.get(),
            "recv_hex": self.recv_hex.get(),
            "auto_newline": self.auto_newline.get(),
        }
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"Save config failed: {e}")

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Mode").grid(row=0, column=0, sticky="w")
        mode_box = ttk.Combobox(
            top,
            textvariable=self.mode,
            values=["tcp_client", "tcp_server", "udp"],
            state="readonly",
            width=12,
        )
        mode_box.grid(row=0, column=1, padx=6)
        self.mode_box = mode_box

        ttk.Label(top, text="Host").grid(row=0, column=2, sticky="w")
        self.host_box = ttk.Combobox(top, textvariable=self.host, values=self.host_history, width=20)
        self.host_box.grid(row=0, column=3, padx=6)

        ttk.Label(top, text="Port").grid(row=0, column=4, sticky="w")
        self.port_box = ttk.Combobox(top, textvariable=self.port, values=self.port_history, width=8)
        self.port_box.grid(row=0, column=5, padx=6)

        ttk.Label(top, text="Encoding").grid(row=0, column=6, sticky="w")
        self.encoding_box = ttk.Combobox(
            top,
            textvariable=self.encoding,
            values=["gbk", "gb2312", "utf-8", "latin1"],
            state="readonly",
            width=8,
        )
        self.encoding_box.grid(row=0, column=7, padx=6)

        self.btn_connect = ttk.Button(top, text="Connect/Start", command=self.connect)
        self.btn_connect.grid(row=0, column=8, padx=6)

        self.btn_disconnect = ttk.Button(top, text="Disconnect/Stop", command=self.disconnect)
        self.btn_disconnect.grid(row=0, column=9, padx=6)

        mid = ttk.Frame(self.root, padding=(8, 0))
        mid.pack(fill=tk.X)
        ttk.Checkbutton(mid, text="Send HEX", variable=self.send_hex).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(mid, text="Recv HEX", variable=self.recv_hex).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(mid, text="Auto \\r\\n", variable=self.auto_newline).pack(side=tk.LEFT, padx=4)

        log_frame = ttk.Frame(self.root, padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(log_frame, text="Receive / Log").pack(anchor="w")

        self.text_recv = tk.Text(log_frame, height=22, wrap="word")
        self.text_recv.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scroll = ttk.Scrollbar(log_frame, command=self.text_recv.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_recv.configure(yscrollcommand=scroll.set)

        send_frame = ttk.Frame(self.root, padding=8)
        send_frame.pack(fill=tk.BOTH)
        ttk.Label(send_frame, text="Send").pack(anchor="w")
        self.text_send = tk.Text(send_frame, height=6, wrap="word")
        self.text_send.pack(fill=tk.BOTH, expand=True)
        self.text_send.bind("<Return>", self._on_enter_send)
        self.text_send.bind("<Shift-Return>", self._on_shift_enter_newline)

        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill=tk.X)
        ttk.Button(bottom, text="Send", command=self.send_data).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Clear Log", command=lambda: self.text_recv.delete("1.0", tk.END)).pack(side=tk.LEFT, padx=6)
        self._bind_shortcuts()

    def _bind_shortcuts(self):
        for widget in [self.host_box, self.port_box, self.mode_box, self.encoding_box]:
            widget.bind("<Control-a>", self._select_all_entry)
            widget.bind("<Control-A>", self._select_all_entry)
            widget.bind("<FocusOut>", lambda _event: self._save_config())
        for widget in [self.text_recv, self.text_send]:
            widget.bind("<Control-a>", self._select_all_text)
            widget.bind("<Control-A>", self._select_all_text)

    def _select_all_entry(self, event):
        event.widget.select_range(0, tk.END)
        event.widget.icursor(tk.END)
        return "break"

    def _select_all_text(self, event):
        event.widget.tag_add(tk.SEL, "1.0", tk.END)
        event.widget.mark_set(tk.INSERT, "1.0")
        event.widget.see(tk.INSERT)
        return "break"

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.text_recv.insert(tk.END, f"[{ts}] {msg}\n")
        self.text_recv.see(tk.END)

    def _queue_log(self, msg: str):
        self.recv_queue.put(("log", msg))

    def _queue_data(self, direction: str, data: bytes):
        self.recv_queue.put((direction, data))

    def _drain_queue(self):
        try:
            while True:
                item = self.recv_queue.get_nowait()
                kind = item[0]
                if kind == "log":
                    self.log(item[1])
                else:
                    direction, data = item
                    if self.recv_hex.get():
                        text = data.hex(" ")
                    else:
                        enc = self.encoding.get()
                        text = data.decode(enc, errors="replace")
                    self.log(f"{direction} ({self.encoding.get()}, {len(data)} bytes): {text}")
        except queue.Empty:
            pass
        self.root.after(100, self._drain_queue)

    def _parse_target(self):
        host = self.host.get().strip()
        try:
            port = int(self.port.get().strip())
        except ValueError:
            raise ValueError("Port must be an integer")
        if port < 1 or port > 65535:
            raise ValueError("Port out of range 1-65535")
        if not host:
            raise ValueError("Host cannot be empty")
        return host, port

    def connect(self):
        if self.connected or self.running:
            self.log("Already running")
            return

        try:
            host, port = self._parse_target()
            mode = self.mode.get()
            self._save_config()

            self.stop_event.clear()
            if mode == "tcp_client":
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(5)
                self.sock.connect((host, port))
                self.sock.settimeout(None)
                self.connected = True
                self.running = True
                self.recv_thread = threading.Thread(target=self._recv_loop_client, daemon=True)
                self.recv_thread.start()
                self.log(f"TCP Client connected to {host}:{port}")

            elif mode == "tcp_server":
                self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_sock.bind((host, port))
                self.server_sock.listen(1)
                self.server_sock.settimeout(1.0)
                self.running = True
                self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
                self.accept_thread.start()
                self.log(f"TCP Server listening on {host}:{port}")

            elif mode == "udp":
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.bind((host, port))
                self.running = True
                self.connected = True
                self.recv_thread = threading.Thread(target=self._recv_loop_udp, daemon=True)
                self.recv_thread.start()
                self.log(f"UDP bound on {host}:{port}")
            else:
                raise ValueError("Unsupported mode")

        except Exception as e:
            self.log(f"Connect/start failed: {e}")

    def disconnect(self):
        self.stop_event.set()
        self.running = False
        self.connected = False

        for s in [self.client_sock, self.server_sock, self.sock]:
            if s:
                try:
                    s.close()
                except Exception:
                    pass

        self.client_sock = None
        self.server_sock = None
        self.sock = None
        self.client_addr = None
        self.log("Stopped")

    def _accept_loop(self):
        while not self.stop_event.is_set():
            try:
                client, addr = self.server_sock.accept()
                if self.client_sock:
                    try:
                        self.client_sock.close()
                    except Exception:
                        pass
                self.client_sock = client
                self.client_addr = addr
                self.connected = True
                self._queue_log(f"Client connected: {addr[0]}:{addr[1]}")
                t = threading.Thread(target=self._recv_loop_server_client, daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                self._queue_log(f"Accept error: {e}")
                break

    def _recv_loop_client(self):
        while not self.stop_event.is_set() and self.sock:
            try:
                data = self.sock.recv(4096)
                if not data:
                    self._queue_log("Remote closed")
                    break
                self._queue_data("RX", data)
            except OSError:
                break
            except Exception as e:
                self._queue_log(f"Recv error: {e}")
                break
        self.connected = False

    def _recv_loop_server_client(self):
        c = self.client_sock
        while not self.stop_event.is_set() and c:
            try:
                data = c.recv(4096)
                if not data:
                    self._queue_log("Client disconnected")
                    break
                self._queue_data("RX", data)
            except OSError:
                break
            except Exception as e:
                self._queue_log(f"Client recv error: {e}")
                break

    def _recv_loop_udp(self):
        while not self.stop_event.is_set() and self.sock:
            try:
                data, addr = self.sock.recvfrom(4096)
                self.client_addr = addr
                self._queue_log(f"UDP from {addr[0]}:{addr[1]}")
                self._queue_data("RX", data)
            except OSError:
                break
            except Exception as e:
                self._queue_log(f"UDP recv error: {e}")
                break

    def _build_payload(self, raw: str) -> bytes:
        if self.auto_newline.get():
            raw += "\r\n"
        if self.send_hex.get():
            cleaned = raw.replace(" ", "").replace("\n", "").replace("\r", "")
            if len(cleaned) % 2 != 0:
                raise ValueError("HEX length must be even")
            return bytes.fromhex(cleaned)
        return raw.encode(self.encoding.get(), errors="replace")

    def send_data(self):
        raw = self.text_send.get("1.0", tk.END).rstrip("\n")
        if not raw:
            self.log("Nothing to send")
            return

        try:
            self._save_config()
            payload = self._build_payload(raw)
            mode = self.mode.get()

            if mode == "tcp_client":
                if not self.sock:
                    raise RuntimeError("Not connected")
                self.sock.sendall(payload)
                self._queue_data("TX", payload)
                self._queue_log(f"Sent {len(payload)} bytes, HEX: {payload.hex(' ')}")

            elif mode == "tcp_server":
                if not self.client_sock:
                    raise RuntimeError("No client connected")
                self.client_sock.sendall(payload)
                self._queue_data("TX", payload)
                self._queue_log(f"Sent {len(payload)} bytes, HEX: {payload.hex(' ')}")

            elif mode == "udp":
                if not self.sock:
                    raise RuntimeError("UDP not started")
                host, port = self._parse_target()
                target = self.client_addr if self.client_addr else (host, port)
                self.sock.sendto(payload, target)
                self._queue_log(f"UDP to {target[0]}:{target[1]}")
                self._queue_data("TX", payload)
                self._queue_log(f"Sent {len(payload)} bytes, HEX: {payload.hex(' ')}")

            self.text_send.delete("1.0", tk.END)

        except Exception as e:
            self.log(f"Send failed: {e}")

    def _on_enter_send(self, event):
        self.send_data()
        return "break"

    def _on_shift_enter_newline(self, event):
        self.text_send.insert(tk.INSERT, "\n")
        return "break"

    def on_close(self):
        self._save_config()
        self.disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    app = NetDebugTool(root)
    app.log("Ready")
    root.mainloop()


if __name__ == "__main__":
    main()
