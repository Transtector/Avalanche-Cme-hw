import time
import memcache

sharedmem = memcache.Client(['127.0.0.1:11211'],debug=0)
print sharedmem

while(1):

    time.sleep(1);
    status = sharedmem.get('status')
    print(status['channels'][0]['sensors'][0]['data'][0][1])
