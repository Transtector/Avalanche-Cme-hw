import time
import curses

def pbar(window):
    #for i in range(10):
    i = 0;
    while(1):
        window.addstr(0,0,"["+("="*i)+">"+(" "*(10-i))+"]")
        window.refresh()
        time.sleep(0.5)
        i += 1
        if i > 10:
            i = 0


curses.wrapper(pbar)
