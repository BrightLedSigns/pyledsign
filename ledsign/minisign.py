import sys
from ledsign import LedSign, LedSignFactory
class MiniSign(LedSign):
    SLOTRANGE=range(1,9)
    EFFECTMAP = dict(
        hold=0x41, scroll=0x42, snow=0x43, 
        flash=0x44, hold_flash=0x45
    )
    SPMAP = {1:0x31, 2:0x32, 3:0x33, 4:0x34, 5:0x35}
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

    def queuepix(this,**params):
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


    def queueicon(this,**params):
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

    def queuemsg(this,**params):
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
        if not 'effect' in params:
            params['effect']="scroll"
        else:
            if not params['effect'] in MiniSign.EFFECTMAP:
                raise Exception('Invalid effect value ['+
                  params['effect'] + ']'
                )
                return None
        msgobj=this.factory.msg(
            devicetype=this.devicetype,
            **params
        )

    def sendq(this,**params):
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
                this.writeserial(barray(packet))
                # sleep to avoid overrunning serial buffers on the sign
                sleep(params['packetdelay'])

        # data other than messages
        for packet in this.packets():
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
            bits+=BITVALS[slot]
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
        if this.speed in MiniSign.SPMAP:
            speed=MiniSign.SPMAP[this.speed]
        else:
            speed=MiniSign.SPMAP[5]

        if this.effect in MiniSign.EFFECTMAP:
            effect=MiniSign.EFFECTMAP[this.effect]
        else:
            effect=MiniSign.EFFECTMAP['hold']

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
        this.objtype='icon'
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

class MiniSignClipart():
    def _init(this, **params):
       if not 'type' in params:
           raise Exception('Parameter [type] must be supplied (pix or icon)')
       if params['type'] != "pix" and params['slot'] != "icon":
           raise Exception('Parameter [type] invalid, must be pix or icon')
       this.type=params.type 
       if 'name' in params:
           this.name=params.name
           if 0:
               raise Exception('No clipart named [%s] exists',)
    def data(this):
        pass
    def width(this):
        pass
    def height(this):
        pass
    def hash(this, **params):
        name=params.name;
        CLIPART_PIX=dict(
        zen16=dict(
            width=16,
            height=16,
            data=(
             '07e00830100820045c067e02733273327f027f863ffc1ff80ff007e000000000'
            )
        ),
        zen12=dict(
            width=12,
            height=12,
            data=('0e00318040404040f120f860dfe07fc07fc03f800e000000')
        ),
        cross16=dict(
            width=16,
            height=16,
            data=(
             '0100010001000100010002800440f83e04400280010001000100010001000100'
            )
        ),
        circle16=dict(
            width=16,
            height=16,
            data=(
             '07e00ff01ff83ffc7ffe7ffe7ffe7ffe7ffe7ffe3ffc1ff80ff007e000000000'
            )
        ),
        questionmark12=dict(
            width=12,
            height=12,
            data=('1f003f8060c060c061800300060006000600000006000600')
        ),
        smile12=dict(
            width=12,
            height=12,
            data=('0e003180404051408020802091204e40404031800e000000')
        ),
        phone16=dict(
            width=16,
            height=16,
            data=(
             '000000003ff8fffee00ee44ee44e0fe0183017d017d037d8600c7ffc00000000'
            )
        ),
        rightarrow12=dict(
            width=12,
            height=12,
            data=('000000000000010001807fc07fe07fc00180010000000000')
        ),
        heart12=dict(
            width=12,
            height=12,
            data=('000071c08a208420802080204040208011000a0004000000')
        ),
        heart16=dict(
            width=16,
            height=16,
            data=(
             '00000000000000000c6012902108202820081010101008200440028001000000'
            )
        ),
        square12=dict(
            width=12,
            height=12,
            data=('fff0fff0fff0fff0fff0fff0fff0fff0fff0fff0fff0fff0')
        ),
        handset16=dict(
            width=16,
            height=16,
            data=(
             '00003c003c003e0006000600060c065006a0075006503e603c003c0000000000'
            )
        ),
        leftarrow16=dict(
            width=16,
            height=16,
            data=(
             '00000000000004000c001c003ff87ff83ff81c000c0004000000000000000000'
            )
        ),
        circle12=dict(
            width=12,
            height=12,
            data=('0e003f807fc07fc0ffe0ffe0ffe07fc07fc03f800e000000')
        ),
        questionmark16=dict(
            width=16,
            height=16,
            data=(
             '000000000fc01fe0303030303030006000c00180030003000000030003000000'
            )
        ),
        smile16=dict(
            width=16,
            height=16,
            data=(
              '07c01830200840044c648c62800280028002882247c440042008183007c00000'
            )
        ),
        leftarrow12=dict(
            width=12,
            height=12,
            data=('000000000000080018003fe07fe03fe01800080000000000')
        ),
        rightarrow16=dict(
            width=16,
            height=16,
            data=(
             '000000000000008000c000e07ff07ff87ff000e000c000800000000000000000'
            )
        ),
        music16=dict(
            width=16,
            height=16,
            data=(
             '000001000180014001200110011001200100010007000f000f000e0000000000'
            )
        ),
        phone12=dict(
            width=12,
            height=12,
            data=('00007fc0ffe0c060c060ca601f0031802e806ec0c060ffe0')
        ),
        music12=dict(
            width=12,
            height=12,
            data=('000008000c000a0009000880088039007800780070000000')
        ),
        cross12=dict(
            width=12,
            height=12,
            data=('04000400040004000a00f1e00a0004000400040004000000')
        ),
        handset12=dict(
            width=12,
            height=12,
            data=('f000f80018001800180018201b401c801940f880f0000000')
        ),
        square16=dict(
            width=16,
            height=16,
            data=(
             'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
            )
        ),
        );
        CLIPART_ICONS=dict(
        cross16=dict(
            width=32,
            height=16,
            data=(
             '01000100010001000100010001000100010002800280044004400820F83EF01E'
             '0440082002800440010002800100010001000100010001000100010001000100'
            )
        ),
        heart16=dict(
            width=32,
            height=16,
            data=(
             '000000000000000000001C70000022880C604104129040242108402420284004'
             '2008200810102008101010100820082004400440028002800100010000000000'
            )
        ),
        leftarrow16=dict(
            width=32,
            height=16,
            data=(
             '000000000000000000000000040000000C0004001C000C003FF81C007FF83FF8'
             '3FF87FF81C003FF80C001C0004000C0000000400000000000000000000000000'
            )
        ),
        rightarrow16=dict(
            width=32,
            height=16,
            data=(
             '0000000000000000000000000080000000C0008000E000C07FF000E07FF87FF0'
             '7FF07FF800E07FF000C000E0008000C000000080000000000000000000000000'
            )
        ),
        handset16=dict(
            width=32,
            height=16,
            data=(
             '000000003C003C003C003C003E003E000600060006000600060C06000650064C'
             '06A006B007500748065006503E603E203C003C003C003C000000000000000000'
            )
        ),
        phone16=dict(
            width=32,
            height=16,
            data=(
             '0000000000003FF83FF8FFFEFFFEE00EE00EE00EE44EE44EE44E04400FE00FE0'
             '1830183017D017D017D017D037D837D8600C600C7FFC7FFC0000000000000000'
            )
        ),
        smile16=dict(
            width=32,
            height=16,
            data=(
             '07C007C01830183020082008400440044C644C648C628C628002800280028002'
             '800290128822983247C44C64400447C4200820081830183007C007C000000000'
            )
        ),
        circle16=dict(
            width=32,
            height=16,
            data=(
             '07E000000FF007E01FF80FF03FFC1FF87FFE3FFC7FFE3FFC7FFE3FFC7FFE3FFC'
             '7FFE3FFC7FFE3FFC3FFC1FF81FF80FF00FF007E007E000000000000000000000'
            )
        ),
        zen16=dict(
            width=32,
            height=16,
            data=(
             '07E00000083007E010080830200410085C0620047E025C0673327E0273327332'
             '7F0273327F867F023FFC7F861FF83FFC0FF01FF807E00FF0000007E000000000'
            )
        ),
        music16=dict(
            width=32,
            height=16,
            data=(
             '0000000001000000018001000140018001200140011001200110011001200110'
             '0100012001000100070007000F000F000F000F000E000E000000000000000000'
            )
        ),
        questionmark16=dict(
            width=32,
            height=16,
            data=(
             '00000000000000000FC000001FE00FC030301FE0303030303030303000600060'
             '00C000C001800180030003000300030000000000030003000300030000000000'
            )
        ),
        square16=dict(
            width=32,
            height=16,
            data=(
             'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
             'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
            )
        ),
        cross12=dict(
            width=24,
            height=12,
            data=(
              '0400400400400400400400a00a0110f1ee0e'
              '0a01100400a0040040040040040040000000'
            )
        ),
        heart12=dict(
            width=24,
            height=12,
            data=(
             '00000071c0008a200084271c8028a2802842'
             '4044042082081101100a00a0040040000000'
            )
        ),
        leftarrow12=dict(
            width=24,
            height=12,
            data=(
             '0000000000000001000803001807fc3feffc'
             '7fe7fc3fe300180100080000000000000000'
            )
        ),
        rightarrow12=dict(
            width=24,
            height=12,
            data=(
             '000000000000000020010030018ff87fcffc'
             '7feff87fc030018020010000000000000000'
            )
        ),
        handset12=dict(
            width=24,
            height=12,
            data=(
             'f00f00f80f80180180180180180182182194'
             '1b41a81c81d4194188f88f80f00f00000000'
            )
        ),
        phone12=dict(
            width=24,
            height=12,
            data=(
             '0000007fc000ffe7fcc06ffec06c06ca6ca6'
             '1f01f03183182e82e86ec6ecc06c06ffeffe'
            )
        ),
        smile12=dict(
            width=24,
            height=12,
            data=(
             '0e00e0318318404404514514802802802802'
             '9129b24e44444044043183180e00e0000000'
            )
        ),
        circle12=dict(
            width=24,
            height=12,
            data=(
             '0e00003f80e07fc3f87fc3f8ffe7fcffe7fc'
             'ffe7fc7fc3f87fc3f83f80e00e0000000000'
            )
        ),
        zen12=dict(
            width=24,
            height=12,
            data=(
             '0e00003180e0404318404404f12404f86f12'
             'dfef867fcdfe7fc7fc3f87fc0e03f80000e0'
            )
        ),
        music12=dict(
            width=24,
            height=12,
            data=(
             '0000000801000c01800a0140090120088120'
             '088120390740780f00780f00700e00000000'
            )
        ),
        questionmark12=dict(
            width=24,
            height=12,
            data=(
             '1f00003f81e060c3f060c618618618030630'
             '0600600600c00600c00000000600c00600c0'
            )
        ),
        square12=dict(
            width=24,
            height=12,
            data=(
              'ffffffffffffffffffffffffffffffffffff'
              'ffffffffffffffffffffffffffffffffffff'
            )
        )

        )
        if ( this.type == "icon" ):
            return CLIPART_ICONS;
        elif ( this.type == "pix" ):
            return CLIPART_PIX;
