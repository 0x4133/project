import socket
import subprocess
import threading
import webbrowser
from tkinter import Tk, ttk, Button, Scrollbar, VERTICAL, RIGHT, Y, LEFT, BOTH

from scapy.all import ARP, Ether, srp


def scan_network(subnet: str):
    """Scan subnet using ARP requests."""
    arp = ARP(pdst=subnet)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    result = srp(packet, timeout=3, verbose=False)[0]
    devices = []
    for _, received in result:
        ip = received.psrc
        mac = received.hwsrc
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except socket.herror:
            hostname = ""
        devices.append({"ip": ip, "mac": mac, "hostname": hostname})
    return devices


class NetworkGUI:
    def __init__(self, root, subnet="192.168.1.0/24"):
        self.root = root
        self.subnet = subnet
        self.tree = ttk.Treeview(
            root, columns=("ip", "hostname", "mac"), show="headings"
        )
        self.tree.heading("ip", text="IP")
        self.tree.heading("hostname", text="Hostname")
        self.tree.heading("mac", text="MAC")
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll = Scrollbar(root, orient=VERTICAL, command=self.tree.yview)
        scroll.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscroll=scroll.set)
        self.tree.tag_configure("active", background="lightgreen")
        self.tree.bind("<Double-1>", self.on_double_click)
        Button(root, text="Scan", command=self.scan).pack(side=LEFT)
        self.webssh_process = None

    def start_webssh(self):
        if self.webssh_process is None or self.webssh_process.poll() is not None:
            self.webssh_process = subprocess.Popen(
                [
                    "wssh",
                    "--address",
                    "127.0.0.1",
                    "--port",
                    "8888",
                    "--policy",
                    "autoadd",
                    "--redirect",
                    "False",
                ]
            )

    def scan(self):
        def _scan():
            devices = scan_network(self.subnet)
            self.tree.delete(*self.tree.get_children())
            for dev in devices:
                self.tree.insert(
                    "",
                    "end",
                    values=(dev["ip"], dev["hostname"], dev["mac"]),
                    tags=("active",),
                )

        threading.Thread(target=_scan, daemon=True).start()

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        ip = self.tree.item(item[0], "values")[0]
        self.start_webssh()
        webbrowser.open(f"http://localhost:8888/?hostname={ip}&port=22")


def main():
    root = Tk()
    root.title("Network Scanner")
    app = NetworkGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
