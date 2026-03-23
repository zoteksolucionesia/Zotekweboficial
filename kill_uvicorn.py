import psutil

def main():
    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and 'uvicorn' in ' '.join(cmdline):
                print(f"Killing uvicorn PID {proc.info['pid']} - {cmdline}")
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    print(f"Killed {killed} processes")

if __name__ == '__main__':
    main()
