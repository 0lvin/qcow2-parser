# qcow2-parser
Parser for qcow2 format

# test image create
```bash
dd if=/dev/zero of=zero.raw count=1024
qemu-img convert zero.raw zero.qcow2 -f raw -O qcow2
dd if=/dev/urandom of=random.raw count=1024
qemu-img convert random.raw random.qcow2 -f raw -O qcow2
```
