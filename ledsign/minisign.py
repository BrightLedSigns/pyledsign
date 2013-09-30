import sys
from ledsign import LedSign, LedSignFactory
class MiniSign(LedSign):
    SLOTRANGE=range(1,9)
    def _init(this):
        if not hasattr(this,'devicetype'):
            raise Exception('Devicetype not supplied')
        if this.devicetype != "sign" and this.devicetype != "badge":
            raise Exception('Invalid value for devicetype [' +this.devicetype+
                ']');
        this.factory=MiniSignFactory()
        this.factory.initslots(
            slotrange=MiniSign.SLOTRANGE
        )

    def _factory(this):
        return this.factory

    def addpix(this,**params):
        if 'clipart' in params:
            ca=MiniSignClipart(
                name=params.clipart,
                type='pix'
            ) 
            params['data']=ca.data
            params['width']=ca.width
            params['height']=ca.height
        if not 'data' in params:
            raise Exception('Parameter [data] must be present')
            return None
        pixobj=this.factory.pixmap(
            devicetype=this.devicetype,
            **params
        )        
        imagetag=this.settag(pixobj)
        return imagetag


    def addicon(this,**params):
        if 'clipart' in params:
            ca=MiniSignClipart(
                name=params.clipart,
                type='icon'
            ) 
            params['data']=ca.data
        if not 'data' in params:
            raise Exception('Parameter [data] must be present')
            return None
        iconobj=this.factory.icon(
            data=params['data'],
            devicetype=this.devicetype
        )        
        return this.settag(iconobj)

    def addmsg(this,**params):
        maxmsg=len(this.factory.slotrange)
        #if this.msgcount > maxmsg:
        if 0 > maxmsg:
            raise Exception('Maximim message count of '+maxmsg+' is already'+
                ' reached, discarding new message')
            return None 
        if not 'data' in params:
            raise Exception('Parameter [data] must be present')
            return None
        if not 'speed' in params:
            params['speed']=5
        params['speed']=int(params['speed'])
        if params['speed'] < 1 or params['speed'] > 5:
            raise Exception('Parameter [speed] must be between 1 and 5')
            return None 
        if not 'effects' in params:
            params['effect']="scroll"
        else:
            if not params['effect'] in EFFECTMAP:
                raise Exception('Invalid effect value ['+
                  params['effect'] + ']'
                )
                return None
        msgobj=this.factory.msg(
            devicetype=this.devicetype,
            **params
        )

    def send(this,**params):
        from sys import hexversion
        from time import sleep
        from struct import pack
        if sys.hexversion < 0x02060000:
            def barray(n): return(n)
        else:   
            def barray(n): return(bytearray(n))

        if not 'device' in params:
            raise Exception('Parameter [device] must be supplied')

        if not 'baudrate' in params:
            params['baudrate']=38400

        if not 'packetday' in params:
            params['packetdelay']=0.20
        else:
            params['packetdelay']=float(params['packetdelay'])

        this.connectserial(
            device=params['device'],
            baudrate=params['baudrate'],
        )
            #debug=1
        this.writeserial(barray([0]))
        count=0
        for msgobj in this.factory.objects('msg'):
            count+=1
            msgobj.data=this.processtags(msgobj.data)
            for packet in msgobj.codify():
                mlen=len(packet)
                sys.stdout.write('writing message packet [%d] bytes\n' % mlen)
                this.writeserial(barray(packet))
                # sleep to avoid overrunning serial buffers on the sign
                sleep(params['packetdelay'])

        # data other than messages
        for packet in this.packets():
            sys.stdout.write('writing misc packet\n');
            this.writeserial(barray(packet))
            sleep(params['packetdelay'])

        if 'showslots' in params:
            showslots=params['showslots']
        else:
            showslots=None
        bits=this.factory.getshowbits(showslots)
        if bits != 0:
            this.writeserial(barray([0x02,0x33,bits]))
        this.serialclose()

    def packets(this):
        blob=''.join(this.factory.chunks)
        blen=len(blob)
        if blen % 64 != 0:
            paddedsize=blen+64-(blen % 64)
            blob += '\x00' * (paddedsize-len(blob))
        newlen=len(blob)
        count=0x0E00
        packets=[]
        for chunk in [blob[i:i+64] for i in range(0,len(blob),64)]:
            tosend=[]
            clen=len(chunk)
            tosend.extend([0x02,0x31])
            hcount='%04x'%count
            start=int(hcount[0:2],16)
            end=int(hcount[2:4],16)
            tosend.extend([start,end])
            total=0
            # checksum
            for char in list(chunk):
                tosend.append(ord(char))
            for num in tosend[1:]:
                total+=num
            tosend.append(total % 256)
            packets.append(tosend)
            count+=64
        return packets

    def processtags(this,data):
        from struct import pack
        if this.devicetype == "badge":
            normal=pack('BB',0xff,0x80)
            flash=pack('BB',0xff,0x81)
        else:
            normal=pack('BB',0xff,0x8f)
            flash=pack('BB',0xff,0x8f)
        #
        # this use of casting a bytes() type to a latin-1 str
        # is cheating a  bit to maintain compatibility across 
        # python v2 and v3. 
        #
        # latin-1 has an encoding for all single bytes values
        # from 0-255.  It's ugly, but works
        #
        if sys.hexversion < 0x03000000:
            data=data.replace('<f:normal>',normal)
            data=data.replace('<f:flash>',flash)
        else:   
            data=data.replace('<f:normal>',str(normal,'latin-1'))
            data=data.replace('<f:flash>',str(flash,'latin-1'))
    
        import re
        for match in re.findall(r'(<i:\d+>)',data):
            if sys.hexversion < 0x03000000:
                data=data.replace(match,this.gettag(match))
            else:
                data=data.replace(match,str(this.gettag(match),'latin-1'))
        return data


class MiniSignFactory(LedSignFactory):

    def _init(this):         
        this.chunkcache=dict()
        this.chunks=[]
        this.objlist=dict()
        this.objlist['msg']=[]
        this.objlist['pixmap']=[]
        this.objlist['icon']=[]

    def msg(this,**params):
        obj=MiniSignMsg(
            factory=this,
            **params
        )
        this.add_object(obj)
        return obj

    def pixmap(this,**params):
        obj=MiniSignPixmap(
            factory=this,
            **params
        )
        this.add_object(obj)
        return obj

    def icon(this,**params):
        obj=MiniSignIcon(
            factory=this,
            **params
        )
        this.add_object(obj)
        return obj

    def add_chunk(this, **params):
        from struct import pack
        objtype=params['objtype']
        format=params['format']
        retval=''
        bstr=params['chunk']
        chunk=''
        for byte in [bstr[i:i+8] for i in range(0,len(bstr),8)]:
            char=chr(int(byte,2))
            chunk+=char
        if chunk in this.chunkcache:
            retval=this.chunkcache[chunk]
        else:
            sequence=0
            for thing in this.chunks:
                tlen=len(thing)
                if tlen > 32:
                    sequence+=2
                else:
                    sequence+=1
            this.chunks.append(chunk)
            if objtype == 'pixmap':
                msgref=0x8000+sequence
            elif objtype == 'icon':
                msgref=0xC000+sequence
            else:
                raise Exception('Unsupported Object type [%s]' % objtype)
            retval=pack('!H',msgref)
            this.chunkcache[chunk]=retval
        return retval

    def getshowbits(this,showslots):
        BITVALS={1:1, 2:2, 3:4, 4:8, 5:16, 6:32, 7:64, 8:128}
        bits=0
        if showslots != None:
            slotlist=showslots
        else:   
            slotlist=this.usedslots
        for slot in slotlist:
            sys.stdout.write('adding bitval [%d]\n' %slot)
            bits+=BITVALS[slot]
        sys.stdout.write('showbits is [%d]\n' % bits)
        return bits
            

class MiniSignMsg:
    def __init__(this, **params):
        this.objtype='msg'
        if 'slot' in params:
            if params['slot'] < 1 or params['slot'] > 8:
                raise Exception('Parameter [slot] must be a value from 1 to 8')
            else:
                slot=params['slot']
        else:
            slot=None
        for a,b in params.items():
            setattr(this,a,b)
        this.slot=this.factory.setslot(slot)

    def codify(this):
        from struct import pack
        SPMAP = {1:0x31, 2:0x32, 3:0x33, 4:0x34, 5:0x35}
        EFFECTMAP = dict(
            hold=0x41, scroll=0x42, snow=0x43, 
            flash=0x44, hold_flash=0x45
        )
        if this.speed in SPMAP:
            speed=SPMAP[this.speed]
        else:
            speed=SPMAP[5]

        if this.effect in EFFECTMAP:
            effect=EFFECTMAP[this.effect]
        else:
            effect=EFFECTMAP['hold']

        data=this.data
        mlen=len(data)
        # why this? because ljust doesn't accept pad chars in python2.3
        data += '\x00' * (255-mlen)
        encoded=[]
        endmem=[0x00,0x40,0x80,0xc0]
        for i in range(0,4):
            start=0x06+this.slot-1
            if i == 0:
                chunk=data[0:60]
            else:
                offset=60+(64*(i-1))
                chunk=data[offset:offset+64]
            end=endmem[i]
            csize=len(chunk)+2
            tosend=[0x02,0x31,start,end]
            if i == 0:
                tosend.extend([speed,0x31,effect,mlen])
            for char in list(chunk):
                tosend.append(ord(char))
            total=0
            #for byte in list(chunk)[1:]:
            for byte in tosend[1:]:
                total+=byte
            tosend.append(total % 256)
            encoded.append(tosend)
        return encoded

class MiniSignImage:
    def __init__(this, **params):
        this.chunkcache=dict()
        this._init(**params)
        this.msgref=this.load()

    def load(this):
        import math
        data=this.data
        width=this.width
        if len(data) < width * this.height:
            data+='0'*((width*this.height)-len(data))
        if width%this.tilesize:
            padding=this.tilesize-(width%this.tilesize)
            newdata=''
            for row in [data[i:i+width] for i in range(0,len(data),width)]:
                newrow=row+'0'*padding
                newdata+=newrow
            data=newdata
            width+=padding
        tiles=int(math.ceil(width/this.tilesize))
        full=''
        for tile in range(1,tiles+1):
            for row in range(1,this.tilesize+1):
                cstart=((tile-1)*this.tilesize)
                offset=((row-1)*width)+cstart
                cend=cstart+this.tilesize
                if row <= this.height:
                    if width >= cstart+this.tilesize:
                        chunk=data[offset:(offset+this.tilesize)]
                    else:
                        chunk=data[offset:(width-cstart)]
                        chunk+='0'*(this.tilesize-len(chunk))
                else:
                    chunk='0'*this.tilesize
                chunk+='0'*(16-len(chunk))
                full+=chunk
        if sys.hexversion < 0x02060000:
            def b():
                return ''
        else:
            def b():
                var=eval("b''")
                return var
        msgref=b() 
        for chunk in [full[i:i+(this.csize*8)] for i in range(0,len(full),(this.csize*8))]:
            newvar=this.factory.add_chunk(
                chunk=chunk,
                objtype=this.objtype,
                format=this.csize
            )
            nvlen=len(newvar)
            msgref+=newvar
        return msgref
            

class MiniSignPixmap(MiniSignImage):
    def _init(this, **params):
        this.objtype='pixmap'
        for a,b in params.items():
            setattr(this,a,b)
        if this.devicetype == 'sign':
            this.tilesize=16
            this.csize=32
        elif this.devicetype == 'badge':
            this.tilesize=12
            this.csize=24

class MiniSignIcon(MiniSignImage):
    def _init(this, **params):
        this.objtype='image'
        for a,b in params.items():
            setattr(this,a,b)
        if this.devicetype == 'sign':
            this.tilesize=16
            this.height=16
            this.width=32
            this.csize=64
        elif this.devicetype == 'badge':
            this.tilesize=12
            this.height=12
            this.width=24
            this.csize=48
