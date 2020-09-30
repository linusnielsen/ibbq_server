from bluepy import btle
import time
import paho.mqtt.client as paho

MAX_RECONNECTION_ATTEMPTS = 10

control_msg = "idle"
ibbq_state = "idle"
temperature = 0
reconnection_attempt = 0

broker="homeserver.local"
#define callback
def on_message(client, userdata, message):
    global control_msg
    msg = str(message.payload.decode("utf-8"))
    print("received message =", msg)
    control_msg = msg

client= paho.Client("client-001")
# Bind function to callback
client.on_message=on_message

 
my_ibbq = "b4:52:a9:b5:7a:05"

#btle.Debugging = True

class MyDelegate(btle.DefaultDelegate):
    def __init__(self, ibbq):
        btle.DefaultDelegate.__init__(self)
        # ... initialise here
        self.ibbq = ibbq

    def handleNotification(self, cHandle, data):
        global temperature
        #print("Notification from handle", cHandle)
        if(cHandle == 0x30):
            temperature = (data[0] + data[1]*256) // 10
            #print("Temperature", temperature)
        # ... perhaps check cHandle
        # ... process 'data'

SETTINGS_RESULT = 0
ACCOUNT_VERIFY  = 1
HISTORY_DATA    = 2
REALTIME_DATA   = 3
SETTINGS_DATA   = 4

class ibbq:
    def __init__(self):
        self.scanner = btle.Scanner()
        self.reset()

    def reset(self):
        self.connected = False
        self.handles = []
        self.devices = None
        self.dev = None

    def scan(self):
        self.devices = None

        # The iBBQ device disconnects regularly, so we need to handle
        # the case when it disconnects in the middle of discovery
        while True:
            try:
                self.devices = self.scanner.scan(20.0)
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
                self.prepare()
                self.login()
                self.enable_realtime_data()
                self.enable_temp_notifications()

                return True
            except:
                pass
 
        print("Failed to connect.")
        return False
        
    def prepare(self):
        self.dev.setDelegate( MyDelegate(self) )
        # The fff0 service is the main service
        svc = ibbq.dev.getServiceByUUID(btle.UUID(0xfff0))
        self.handles = svc.getCharacteristics()

    def login(self):
        print("Logging in...")
        login_message = bytearray([0x21, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0xb8, 0x22, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.handles[ACCOUNT_VERIFY].write(login_message, withResponse = True)

    def enable_realtime_data(self):
        print("Enabling realtime data...")
        enable_message = bytearray([0x0B, 0x01, 0x00, 0x00, 0x00, 0x00])
        self.handles[SETTINGS_DATA].write(enable_message, withResponse = True)

    def enable_temp_notifications(self):
        self.dev.writeCharacteristic(self.handles[REALTIME_DATA].getHandle()+1, bytearray([0x01, 0x00]), withResponse = True)

    def wait_for_notification(self):
        try:
            return self.dev.waitForNotifications(5.0)
        except:
            self.reset()
            return False


ibbq = ibbq()

print("connecting to broker ", broker)
client.connect(broker)
client.loop_start()
print("subscribing ")
client.subscribe("ibbq/control")

def set_state(state):
    global ibbq_state
    print("state: " + ibbq_state + " -> " + state)
    ibbq_state = state
    client.publish("ibbq/state", state)

set_state("idle")

while True:
    if control_msg == "scan":
        print("Scanning...")
        if ibbq.scan():
            print("iBBQ found")
            client.publish("ibbq/response", "found")
        else:
            print("iBBQ not found")
            client.publish("ibbq/response", "not found")
        control_msg = "idle"

    if control_msg == "connect":
        control_msg = "idle"

        set_state("connecting")

        print("Connecting...")
        client.publish("ibbq/response", "connecting")
        if ibbq.connect():
            client.publish("ibbq/response", "running")
            set_state("running")
            reconnection_attempt = 0
        else:
            print("Connection failed")
            client.publish("ibbq/response", "not connected")

    if control_msg != "idle":
        client.publish("ibbq/response", "unknown command: " + control_msg)
        control_msg = "idle"

    if ibbq_state == "running":
        if(ibbq.wait_for_notification()):
            client.publish("ibbq/temp", temperature)
        else:
            print("Realtime data failed")
            set_state("connecting")
    elif ibbq_state == "connecting":
        # Force a reconnection
        if reconnection_attempt < MAX_RECONNECTION_ATTEMPTS:
            reconnection_attempt += 1
            control_msg = "connect"
            time.sleep(5.0)
        else:
            set_state("idle")

    else:
        time.sleep(1.0)
