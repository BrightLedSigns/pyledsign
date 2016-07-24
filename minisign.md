# NAME

MiniSign - Part of the pyledsign python library used to send text and graphics to small LED badges and signs
 

# VERSION

Version 1.01

# SYNOPSIS

    #!/usr/bin/python
    from pyledsign.minisign import MiniSign
    mysign = MiniSign(
        devicetype='sign',
    )
    # queue up a text message
    mysign.queuemsg(
        data='Hello World'
    )
    # queue up a second message
    #   - using the optional effect parameter.
    #     if not supplied, defaults to 'scroll'
    mysign.queuemsg(
        data='MSG 2',
        effect='snow'
    )
    #
    # send the message to the sign via the serial port
    #   note that the sendqueue() method does not empty
    #   the buffer, so if we have a second sign, on a 
    #   different serial port, we can send everything
    #   to it as well...
    #
    mysign.sendqueue(
        device='/dev/ttyUSB0'
    )

# DESCRIPTION

MiniSign is used to send text and graphics via RS232 to our smaller set of LED Signs and badges.

# CONSTRUCTOR

There is only one argument for the constructor...devicetype.  It's a mandatory argument and is used to denote if we're talking a sign (16 pixels high) or a badge (12 pixels high).

    from pyledsign.minisign import MiniSign
    mysign = MiniSign(
        devicetype='sign'
    )
    # $devicetype can be either:
    #   sign  - denoting a device with a 16 pixel high display
    #   badge - denoting a device with a 12 pixel high display

# METHODS

## queuemsg

This family of devices support a maximum of 8 messages that can be sent to the sign.  These messages can consist of three different types of content, which can be mixed together in the same message..plain text, pixmap images, and 2-frame animiated icons.

The queuemsg method has three required arguments...data, effect, and speed:

- __data__:   The data to be sent to the sign. Plain text, optionally with $variables that reference pixmap images or animated icons
- __effect__: One of "hold", "scroll", "snow", "flash" or "hold+flash"
- __speed__:  An integer from 1 to 5, where 1 is the slowest and 5 is the fastest 

The queueMsg method returns a number that indicates how many messages have been created.  This may be helpful to ensure you don't try to add a 9th message, which will fail:

    my mysign=MiniSign.new(devicetype="sign");
    for (1..9) {
         my $number=queuemsg(
             data="Message number $_",
             effect="scroll",
             speed=5
         )
         # on the ninth loop, $number will be undef, and a warning will be
         # generated
    }

## queuepix

The queuepix method allow you to create simple, single color pixmaps that can be inserted into a message. There are two ways to create a picture.

__Using the built-in clipart__

    #
    # load the built-in piece of clipart named phone16
    #   the "16" is hinting that it's 16 pixels high, and thus better suited to
    #   a 16 pixel high device, and not a 12 pixel high device
    #
    pic=mysign.queuepix(
          clipart  ="phone16"
    );
    # now use that in a message
    queuemsg(
        data="here is a phone: %s" % pic,
    );

__Rolling your own pictures__

To supply your own pictures, you need to supply 3 arguments:

__height__: height of the picture in pixels 

__width__: width of the picture in pixels (max is 256)

__data__ : a string of 1's and 0's, where the 1 will light up the pixel and 
a 0 won't.  

    #!/usr/bin/python
    from pyledsign.minisign import MiniSign
    mysign = MiniSign(
        devicetype='sign',
        port='/dev/ttyUSB0',
    )
    # make a 5x5 pixel outlined box 
    pic=mysign.queuepix(
          height=5,
          width =5,
          data  =
            "11111" \
            "10001" \
            "10001" \
            "10001" \
            "11111"
    );
    # now use that in a message
    mysign.queuemsg(
        data="a 5 pixel box: %s" % pic
    );
    mysign.sendqueue(
        device='/dev/ttyUSB0'
    )



## queueicon

The queueicon method is almost identical to the queuepix method. 
The queueicon method accepts either a 16x32 pixel image (for signs), or a 
12x24 pixel image (for badges).  It internally splits the image down the middle
into a left and right halves, each one being 16x16 (or 12x12) pixels.

Then, when displayed on the sign, it alternates between the two, in place, 
creating a simple animation.

    # make an icon using the built-in heart16 clipart
    icon=mysign.queueicon(
        clipart="heart16"
    );
    # now use that in a message
    queuemsg(
        data="Animated heart icon: %s" % icon
    );

You can "roll your own" icons as well.  

    # make an animated icon that alternates between a big box and a small box
    import string
    from pyledsign.minisign import MiniSign
    mysign = MiniSign(
        devicetype='sign',
        port='/dev/ttyUSB0' 
    )
    myicon= \
        "XXXXXXXXXXXXXXXX" + "----------------" \
        "X--------------X" + "----------------" \
        "X--------------X" + "--XXXXXXXXXXX---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--X---------X---" \
        "X--------------X" + "--XXXXXXXXXXX---" \
        "X--------------X" + "----------------" \
        "XXXXXXXXXXXXXXXX" + "----------------"
    # translate X to 1, and - to 0
    myicon=myicon.translate(string.maketrans('X-','10'))
    #
    # no need to specify width or height, as
    # it assumes 16x32 if devicetype is "sign",
    # and 12x24 if devicetype is "badge"
    #
    icon=mysign.queueicon(
        data=myicon
    )
    mysign.queuemsg(
        data="Flashing Icon: [%s]" % icon
    )
    mysign.sendqueue(
        device='/dev/ttyUSB0'
    )
    
## sendqueue


The sendqueue method connects to the sign over RS232 and sends all the data accumulated from prior use of the queuemsg/Pix/Icon methods.  The only mandatory argument is 'device', denoting which serial device to send to.  

It supports three optional arguments: runslots, baudrate, and packetdelay:

- __runslots__: One of either "auto" or "none".  If the runslots parameter is not supplied, it defaults to "auto".
    - auto - with runslots set to auto, a command is sent to the sign to display the message slots that were created by the queued messages sent to the sign.
    - none - with runslots set to none, the messages are still sent to the sign, but no command to display them is sent. The sign will continue to run whatever numbered slots it was showing before the new messages were sent.  Using this in combination with the mysign.sendCmd(runslots,@slots) command allows you full control over which messages are displayed, and when.
- __baudrate__: defaults to 38400, no real reason to use something other than the default, but it's there if you feel the need.  Must be a value that Device::Serialport or Win32::Serialport thinks is valid
- __packetdelay__: An amount of time, in seconds, to wait, between sending packets to the sign.  The default is 0.25, and seems to work well.  If you see "XX" on your sign while sending data, increasing this value may help. Must be greater than zero.  For reference, each text message generates 3 packets, and each 16x32 portion of an image sends one packet.  There's also an additional, short, packet sent after all message and image packets are delivered. So, if you make packetdelay a large number...and have lots of text and/or images, you may be waiting a while to send all the data.

Some examples:

    # typical use on a windows machine
    mysign.sendqueue(
        device='COM4'
    );
    # typical use on a unix/linux machine
    mysign.sendqueue(
        device='/dev/ttyUSB0'
    );
    # using optional arguments, set baudrate to 9600, and sleep 1/2 a second
    # between sending packets.  
    mysign.sendqueue(
        device='COM8',
        baudrate='9600',
        packetdelay=0.5
    );

Note that if you have multiple connected signs, you can send to them without creating a new object:

    # send to the first sign
    mysign.sendqueue(device='COM4');
    # send to another sign
    mysign.sendqueue(device='COM6');
    # send to a badge connected on COM7
    #   this works fine for plain text, but won't work well for
    #   pictures and icons...you'll have to create a new
    #   sign object with devicetype "badge" for them to render correctly
    mysign.sendqueue(device='COM7'); 

# AUTHOR

Kerry Schwab, `<sales at brightledsigns.com>`

# SUPPORT AND BUGS

Please report any bugs or feature requests via GitHub, through the web interface at [https://github.com/BrightLedSigns/pyledsign/issues](https://github.com/BrightLedSigns/pyledsign/issues). 

You may find additional information at our website: [http://www.brightledsigns.com/developers](http://www.brightledsigns.com/developers)

# ACKNOWLEDGEMENTS

Inspiration from similar work:

- [http://zunkworks.com/ProgrammableLEDNameBadges](http://zunkworks.com/ProgrammableLEDNameBadges) - Some code samples for different types of LED badges
- [https://github.com/ajesler/ledbadge-rb](https://github.com/ajesler/ledbadge-rb) - Python library that appears to be targeting signs with a very similar protocol. 

# LICENSE AND COPYRIGHT

Copyright (c) 2013 Kerry Schwab & Bright Signs
All rights reserved.

This program is free software; you can redistribute it and/or modify it
under the terms of the the FreeBSD License . You may obtain a
copy of the full license at:

[http://www.freebsd.org/copyright/freebsd-license.html](http://www.freebsd.org/copyright/freebsd-license.html)


Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

