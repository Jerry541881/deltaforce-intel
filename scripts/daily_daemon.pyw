import os, time, subprocess, datetime, sys

BASE = r'D:\deltaforce-intel\scripts'
LOG = os.path.join(BASE, 'auto_daily.log')
SCRIPT = os.path.join(BASE, 'auto_20s.py')
TARGET_HOUR, TARGET_MIN = 6, 0

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write('[%s] %s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))

def ran_today():
    today = datetime.date.today().strftime('%Y-%m-%d')
    if not os.path.exists(LOG):
        return False
    with open(LOG, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.startswith('[' + today) and ('上传成功' in line or '完成' in line):
                return True
    return False

log('=== 守护进程启动 ===')
while True:
    now = datetime.datetime.now()
    if now.hour == TARGET_HOUR and now.minute == TARGET_MIN:
        if not ran_today():
            log('到点，开始采集')
            try:
                subprocess.run([sys.executable, SCRIPT], cwd=BASE, timeout=600)
            except Exception as e:
                log('采集异常 %s' % e)
        time.sleep(60)
    time.sleep(20)