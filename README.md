# slideshow
Slideshow for Raspberry Pi framebuffer

A simple Python program for show your slides on a screen.
It uses the framebuffer for screen.

Basic operation scans a directory recursively and then generates a random list of
all found catalogs. Looping through this it shows all images and videos in order.

A simple Web-server for controling the slideshow program is included. Functions include
Goto NextDir, Pause, Continue, show image/catalogue, and select a sublist of catalogues
for viewing based on a substring of the catalogue name.
