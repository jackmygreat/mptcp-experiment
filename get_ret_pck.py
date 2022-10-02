#!/usr/bin/python3.7

import pyshark


capture = pyshark.FileCapture('lte-mmwave2-1-0.pcap', display_filter='tcp.analysis.retransmission or tcp.analysis.fast_retransmission')
#capture = pyshark.FileCapture('lte-mmwave2-1-0.pcap', display_filter='tcp.analysis.duplicate_ack')
#capture = pyshark.FileCapture('lte-mmwave2-1-0.pcap', display_filter='tcp.analysis.lost_segment')
retr_cnt = 0

for pckt in capture:
        retr_cnt += 1

print(retr_cnt)
