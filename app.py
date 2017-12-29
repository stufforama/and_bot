import subprocess

while True:
    p = subprocess.Popen(args = r'cert_bot.exe').wait()
    if p != 0:
        continue
    else:
        break