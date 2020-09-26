from bluepy import btle
import binascii
 
my_ibbq = "b4:52:a9:b5:7a:05"

#btle.Debugging = True

class ScanDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device", dev.addr)
        elif isNewData:
            print("Received new data from", dev.addr)

class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        # ... initialise here

    def handleNotification(self, cHandle, data):
        #print("Notification from handle", cHandle)
        if(cHandle == 0x30):
            temp = (data[0] + data[1]*256) / 10.0
            print("Temperature", temp)
        # ... perhaps check cHandle
        # ... process 'data'

SETTINGS_RESULT = 0
ACCOUNT_VERIFY  = 1
HISTORY_DATA    = 2
REALTIME_DATA   = 3
SETTINGS_DATA   = 4

def login(handles):
    print("Logging in...")
    login_message = bytearray([0x21, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0xb8, 0x22, 0x00, 0x00, 0x00, 0x00, 0x00])
    handles[ACCOUNT_VERIFY].write(login_message, withResponse = True)

def enable_realtime_data(handles):
    print("Enabling realtime data...")
    enable_message = bytearray([0x0B, 0x01, 0x00, 0x00, 0x00, 0x00])
    handles[SETTINGS_DATA].write(enable_message, withResponse = True)

# Scan for devices
print("Scanning...")
scanner = btle.Scanner()
#scanner.withDelegate(ScanDelegate())
while True:
    try:
        devices = scanner.scan(20.0)
        break
    except btle.BTLEDisconnectError:
        pass

found = False
for dev in devices:
    #print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
    #for (adtype, desc, value) in dev.getScanData():
    #    print("  %s = %s" % (desc, value))
    if dev.addr == my_ibbq:
        print("Found iBBQ")
        found = True

if found:
    print("Connecting...")
    for attempt in range(5):
        print("Attempt", attempt)
        try:
            dev = btle.Peripheral("b4:52:a9:b5:7a:05")
            break
        except:
            pass
 
    if attempt == 5:
        print("Failed to connect. Exiting...")
        exit()
#    print("Services...")
#    for svc in dev.services:
#        print(str(svc))

    dev.setDelegate( MyDelegate() )

    # The fff0 service is the main service
    svc = dev.getServiceByUUID(btle.UUID(0xfff0))
    handles = svc.getCharacteristics()
#    for ch in handles:
#        print(ch.getHandle(), ch.uuid)

    login(handles)
    enable_realtime_data(handles)
    dev.writeCharacteristic(handles[REALTIME_DATA].getHandle()+1, bytearray([0x01, 0x00]), withResponse = True)

# Main loop --------

while True:
    if dev.waitForNotifications(10.0):
        # handleNotification() was called
        continue

    print("Timeout!")
    # Perhaps do something else here
