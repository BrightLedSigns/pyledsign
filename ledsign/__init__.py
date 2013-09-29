import sys, platform
from platform import python_version
if sys.hexversion < 0x01060000:
    sys.stderr.write('Python 2.6 or newer is required, including version 3.\n')
    sys.stderr.write('  You are running version [%s]\n' % python_version())
    sys.exit(1)
  

class LedSign(object):

    def __init__(this, **params):
        for a,b in params.items():
            setattr(this,a,b)
        this.tags=dict()
        this._init()

    def connectserial(this,**params):
        import sys;
        import serial;
    
        if not 'timeout' in params:
            params['timeout']=5
        if 'debug' in params:
            this.serialdebug=1
            f=open("data.log","ab")
            this.serialdevice=f
        else: 
            try:
                this.serialdevice=serial.Serial(
                    params['device'],
                    params['baudrate'],
                    timeout=params['timeout']
                )
            except serial.serialutil.SerialException:
                e-sys.exc_info()[1]
                raise Exception('Can\'t open serial port: [' + str(e) + ']\n')

    def writeserial(this,data):
        from sys import hexversion
        if hexversion < 0x03000000:
            #map bytestring array back to a string blob for python 2.X
            data=''.join(map(chr,data))
        device=this.serialdevice
        device.write(data)
       

    def serialclose(this):
        device=this.serialdevice
        device.close()

    def settag(this,object):
        number=1
        tag="<i:%d>" % number
        while tag in this.tags:
            tag="<i:%d>" % number
            number+=1
        this.tags[tag]=object.msgref
        return tag

    def gettag(this,tag):
        if tag in this.tags:
            return this.tags[tag]
        else:
            return ''

class LedSignFactory(object):

    def __init__(this, **params):
        for a,b in params.items():
            setattr(this,a,b)
        this._init()
        this.initslots

    def add_object(this,object):
        otype=object.objtype
        this.objlist[otype].append(object)
        return len(this.objlist[otype])

    def objects(this,objtype):
        return this.objlist[objtype]

    def initslots(this,slotrange):
        this.slotrange=list(slotrange)
        this.freeslots=list(slotrange)

    def setslot(this,slot):
        if slot == None:
            if len(this.freeslots) > 0:
                return this.freeslots.pop(0)
            else:   
                raise Exception('Out of slots')
        else:
            if slot in this.freeslots:
                this.freeslots.remove(slot) 
                return slot
            else:
                raise Exception('Slot [%s] not available' % str(slot))
    
