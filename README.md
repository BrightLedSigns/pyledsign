# pyledsign 

pyledsign - Python library to communicate with various models of programmable LED signs
 

## VERSION

Version 1.00

## DESCRIPTION

The pyledsign library is used to send text and graphics to different models of programmable LED signs. We tried to keep the interface consistent across models, and only introduced per-model variations where the underlying capabilities of the sign were different enough to warrant it.  

It has been tested on both Linux and Windows, and should theoretically run anywhere were the [pyserial](http://pyserial.sourceforge.net/) library can run.  The pyserial library is a prerequisite, and allows the protocol messages to be sent via RS232(most common), but also over the network if the sign (or an external network to serial device) supports it. 


## SYNOPSIS

    # "MiniSign" is one specific model
    from ledsign.minisign import MiniSign
    mysign = MiniSign(
        devicetype='sign',
        port='/dev/ttyUSB0',
    ) 
    # addmsg queues a message to be sent with the send method
    mysign.addmsg(
        data='Hello world!'
    )
    mysign.send(
        device='/dev/ttyUSB0'
    )

## USAGE

Since each of the supported signs is a bit different in terms of capability, the usage docs are within the documentation for each type of sign: (links aren't working yet)

- [MiniSign](minisign.md)
- [M500Sign](m500sign.md)

## CAVEATS

- It's possible to overrun the internal memory in a sign/badge by adding too many pixmaps or icons.  We do cache any occurances of identical 16x16 (or 12x12 for badges) blocks within images, which helps a bit.  If you do overrun the memory, you will likely stomp on the storage area for fonts.   Your sign will "work", but display garbled text. The original windows-based software that comes with the sign has functionality to reload the original contents of the memory.

- The internal coding style of this module isn't very Pythonic.  We're trying to maintain this as a straight port of the original code, which was written in Perl.  This makes it easier to add features, fix bugs, etc. 

## AUTHOR

Kerry Schwab, `<sales at brightledsigns.com>`

I am the owner of [BrightLEDSigns.com](http://www.brightledsigns.com/).  Our programmable signs, many of which work with this library, are here: [Programmable Signs from BrightLEDSigns.com](http://www.brightledsigns.com/scrolling-led-signs.html).

Inspiration from similar work:

- [http://zunkworks.com/ProgrammableLEDNameBadges](http://zunkworks.com/ProgrammableLEDNameBadges) - Some technical information on the protocol for different types of LED badges
- [https://github.com/ajesler/ledbadge-rb](https://github.com/ajesler/ledbadge-rb) - Python library that appears to be targeting signs with a very similar protocol to our Mini LED signs and badges. 


## LICENSE AND COPYRIGHT

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
