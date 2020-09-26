from bluepy import btle
import time
import paho.mqtt.client as paho

broker="homeserver.local"
#define callback
def on_message(client, userdata, message):
    time.sleep(1)
    print("received message =",str(message.payload.decode("utf-8")))

client= paho.Client("client-001")
# Bind function to callback
client.on_message=on_message

 
my_ibbq = "b4:52:a9:b5:7a:05"

#btle.Debugging = True

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

class ibbq:
    def __init__(self):
        self.connected = False
        self.handles = []
        self.devices = []
        self.scanner = btle.Scanner()
        self.dev = None

    def scan(self):
        self.devices = None

        # The iBBQ device disconnects regularly, so we need to handle
        # the case when it disconnects in the middle of discovery
        while True:
            try:
                self.devices = self.scanner.scan(10.0)
                for dev in self.devices:
                    #print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
                    #for (adtype, desc, value) in dev.getScanData():
                    #    print("  %s = %s" % (desc, value))
                    if dev.addr == my_ibbq:
                        #print("Found iBBQ")
                        return True
                break
            except btle.BTLEDisconnectError:
                pass
        return False

    def connect(self):
        for attempt in range(5):
            print("Connection attempt %d..." % (attempt+1))
            try:
                self.dev = btle.Peripheral(my_ibbq)
                return True
            except:
                pass
 
        print("Failed to connect.")
        return False
        
    def login(self, handles):
        print("Logging in...")
        login_message = bytearray([0x21, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0xb8, 0x22, 0x00, 0x00, 0x00, 0x00, 0x00])
        handles[ACCOUNT_VERIFY].write(login_message, withResponse = True)

    def enable_realtime_data(self, handles):
        print("Enabling realtime data...")
        enable_message = bytearray([0x0B, 0x01, 0x00, 0x00, 0x00, 0x00])
        handles[SETTINGS_DATA].write(enable_message, withResponse = True)

    def enable_temp_notifications(self, handles):
        self.dev.writeCharacteristic(handles[REALTIME_DATA].getHandle()+1, bytearray([0x01, 0x00]), withResponse = True)


ibbq = ibbq()

# Scan for the iBBQ device
print("Scanning...")
if ibbq.scan():
    print("iBBQ found")

    print("Connecting...")
    if ibbq.connect():
        #print("Services...")
        #for svc in ibbq.dev.services:
        #    print(str(svc))

        ibbq.dev.setDelegate( MyDelegate() )

    # The fff0 service is the main service
        svc = ibbq.dev.getServiceByUUID(btle.UUID(0xfff0))
        handles = svc.getCharacteristics()
#        for ch in handles:
#            print(ch.getHandle(), ch.uuid)

        ibbq.login(handles)
        ibbq.enable_realtime_data(handles)
        ibbq.enable_temp_notifications(handles)

# Main loop --------

        while True:
            if ibbq.dev.waitForNotifications(10.0):
                # handleNotification() was called
                continue

            print("Timeout!")
            # Perhaps do something else here
