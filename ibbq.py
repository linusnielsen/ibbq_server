from bluepy import btle
import time
import paho.mqtt.client as paho


control_msg = "idle"
temperature = 0

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
            temperature = (data[0] + data[1]*256) / 10.0
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
                return True
            except:
                pass
 
        print("Failed to connect.")
        return False
        
    def prepare(self):
        try:
            self.dev.setDelegate( MyDelegate(self) )
            # The fff0 service is the main service
            svc = ibbq.dev.getServiceByUUID(btle.UUID(0xfff0))
            self.handles = svc.getCharacteristics()
            return True
        except:
            self.reset()
            return False

    def login(self):
        print("Logging in...")
        login_message = bytearray([0x21, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0xb8, 0x22, 0x00, 0x00, 0x00, 0x00, 0x00])
        try:
            self.handles[ACCOUNT_VERIFY].write(login_message, withResponse = True)
            return True
        except:
            self.reset()
            return False

    def enable_realtime_data(self):
        print("Enabling realtime data...")
        enable_message = bytearray([0x0B, 0x01, 0x00, 0x00, 0x00, 0x00])
        try:
            self.handles[SETTINGS_DATA].write(enable_message, withResponse = True)
            return True
        except:
            self.reset()
            return False

    def enable_temp_notifications(self):
        try:
            self.dev.writeCharacteristic(self.handles[REALTIME_DATA].getHandle()+1, bytearray([0x01, 0x00]), withResponse = True)
            return True
        except:
            self.reset()
            return False

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

ibbq_state = "idle"

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
        print("Connecting...")
        if ibbq.connect():
            print("iBBQ connected")
            client.publish("ibbq/response", "connected")
            ibbq_state = "connected"
        else:
            print("iBBQ not connected")
            client.publish("ibbq/response", "not connected")
        control_msg = "idle"

    if control_msg == "start":
        print("Starting...")
        control_msg = "idle"
        if not ibbq.prepare():
            print("Prepare failed")
            client.publish("ibbq/response", "not connected")
            ibbq_state = "idle"
            continue
        if not ibbq.login():
            print("Login failed")
            client.publish("ibbq/response", "not connected")
            ibbq_state = "idle"
            continue
        if not ibbq.enable_temp_notifications():
            print("Enable temp notifications failed")
            client.publish("ibbq/response", "not connected")
            ibbq_state = "idle"
            continue
        if not ibbq.enable_realtime_data():
            print("Enable realtime data failed")
            client.publish("ibbq/response", "not connected")
            ibbq_state = "idle"
            continue
        client.publish("ibbq/response", "started")
        ibbq_state = "running"

    if control_msg != "idle":
        client.publish("ibbq/response", "unknown command: " + control_msg)
        control_msg = "idle"

    if ibbq_state == "running":
        if(ibbq.wait_for_notification()):
            client.publish("ibbq/temp", temperature)
        else:
            print("Realtime data failed")
            client.publish("ibbq/response", "not connected")
            ibbq_state = "idle"

    else:
        time.sleep(1.0)
