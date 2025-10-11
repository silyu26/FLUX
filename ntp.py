import os

def sync_ntp_windows(server="time.windows.com"):
    # Run Windows time sync command
    os.system(f"w32tm /config /manualpeerlist:{server} /syncfromflags:manual /update")
    os.system("w32tm /resync")
    print(f"Synced Windows clock with {server}")

sync_ntp_windows()
