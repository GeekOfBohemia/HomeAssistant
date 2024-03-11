from LoggerControl import LoggerControl
from appframe.helpers import twosComplement_hex


lc = LoggerControl()
start = 0x0484
start = 0x0500
start = 0x0680
the_end = start + 59
result = lc.read(start, the_end)
for k, responsereg in result.items():
    try:
        v = twosComplement_hex(responsereg) * 0.01
        # v = int(str(responsereg), 16) * 0.01
    except:
        print(f"Chyba {responsereg}")
        v = 0
    print(k, responsereg, v)
