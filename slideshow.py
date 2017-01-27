#!/usr/bin/python3
# -*- coding: utf-8 -*-
# This Python file uses the following encoding: utf-8
import os
import sys
import random
import time
import threading
import pygame
import web
from urllib import quote_plus
import urllib2
import json
import traceback  #TMP

class imgDirectories():
    def __init__(self, start = './Pictures/'):
        self.root = start
        (self.allDirs, self.dirHier) = self.getDirs(start)
        self.dirList = self.allDirs.keys()
        h = urllib2.urlopen("http://aaphoto/genLists.php?query=listTags")
        self.tagList = json.loads(h.read())
        h.close()

    def rescan(self, start):
        #improve by just rescanning part of the tree
        self.allDirs = self.getDirs(self.root)
        self.dirList = self.allDirs.keys()

    def genListRandom(self, filter = None):
        if filter:
            self.dirList = []
            for dir in self.allDirs.keys():
                if filter in dir.decode('utf-8'):
                    self.dirList.append(dir)
        else:
            self.dirList = self.allDirs.keys()
        return [self.dirList[r] for r in random.sample(xrange(len(self.dirList)),
                                                       len(self.dirList))]
    def getDirs(self, rootdir):
        dirL = {}
        dir = {}
        rootdir = rootdir.rstrip(os.sep)
        start = rootdir.rfind(os.sep) + 1
        for path, dirs, files in os.walk(rootdir):
            dirL[path] = sorted(files)
            folders = path[start:].split(os.sep)
            parent = reduce(dict.get, folders[:-1], dir)
            parent[folders[-1]] = {}
        return (dirL, dir)

class dataThread(threading.Thread):
    def __init__(self):
        super(dataThread, self).__init__()
        self.black = 0, 0, 0
        drivers = ('directfb', 'fbcon', 'svgalib')
        os.putenv('SDL_FBDEV','/dev/fb0')
        os.environ["SDL_FBDEV"] = "/dev/fb0"
        pygame.init()
        self.displaysize = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.displaysize = (1280, 1024) #??
        print 'Disp', self.displaysize
        self.screen = pygame.display.set_mode(self.displaysize,
                                              pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
        self.myfont = pygame.font.SysFont("monospace", 22)
        pygame.mouse.set_visible(False)
        self.imgExt = ['.jpg', '.jpeg', '.gif', '.tiff', '.tif', '.png', '.bmp']
        self.videoExt = ['.mov', '.mp3', '.mp4', '.mpg', '.avi']
        #self.videoExt = []
        self.extOK = self.imgExt + self.videoExt
        self.filename = 'shownDirs.txt'

    def aspect_scale(self, img, (bx,by)):
        """ Scales 'img' to fit into box bx/by.
         This method will retain the original image's aspect ratio """
        ix,iy = img.get_size()
        if ix > iy:
            # fit to width
            scale_factor = bx/float(ix)
            sy = scale_factor * iy
            if sy > by:
                scale_factor = by/float(iy)
                sx = scale_factor * ix
                sy = by
            else:
                sx = bx
        else:
            # fit to height
            scale_factor = by/float(iy)
            sx = scale_factor * ix
            if sx > bx:
                scale_factor = bx/float(ix)
                sx = bx
                sy = scale_factor * iy
            else:
                sy = by
        return pygame.transform.scale(img, (int(sx+0.5),int(sy+0.5))) #+1 round?

    def show(self, dir, fil, wait = False, coord = None):
        ext = os.path.splitext(fil)[1].lower()
        if web.data['mediatype'] == 'image' and ext not in self.imgExt: return
        if web.data['mediatype'] == 'video' and ext not in self.videoExt: return
        if ext not in self.extOK: return
        #print('Show %s in %s' % (fil, dir))
        #print coord
        if wait: t0 = time.time()
        flabel = self.myfont.render(fil, 1, (255,255,0))
        self.screen.fill(self.black)
        if ext in self.imgExt:
            try:
                #img = self.aspect_scale(pygame.image.load(dir+'/'+fil), (1300,1100))
                img = self.aspect_scale(pygame.image.load(dir+'/'+fil), self.displaysize)
                self.screen.blit(img, (0,0))
                #self.screen.blit(self.label, (10, 970))
                #self.screen.blit(self.myfont.render(fil, 1, (255,255,0)), (250, 970))
                text = self.label + ': ' + fil
                self.screen.blit(self.myfont.render(text.replace('data/Pictures/Arkiv ARDO/', ''),
                                                    1, (255,255,0)), (10, 970))
                #IF ZOOM and COORD
                if web.data['zoom'] and coord:
                    (ix1,iy1,ix2,iy2) = img.get_rect()
                    #(x1,y1,x2,y2) = coord
                    x1 = int(coord[0])
                    y1 = int(coord[1])
                    x2 = int(coord[2])
                    y2 = int(coord[3])
                    totsx = 100.0/(x2-x1)
                    totsy = 100.0/(y2-y1)
                    totsc = (totsx+totsy)/2
                    if totsc > 2.5: totsc = 2.5   #limit zoom
                    #mitten på rect (x1+x2)/2 translateras till mitten på bilden (ix1+ix2)/2 vid zoom [ix1=0]
                    tottx = -((x1+x2)/(2.0*100)*ix2*totsc - ix2/2.0)
                    totty = -((y1+y2)/(2.0*100)*iy2*totsc - iy2/2.0)
                    steps = 100
                    #print fil,coord,totsc,tottx,totty
                    #per step
                    sc = (totsc-1)/steps #starting from 1
                    tx = tottx/steps
                    ty = totty/steps
                    for i in range(1, steps):
                        self.screen.blit(pygame.transform.scale(img,
                                         (int(round(ix2*(1+i*sc))), int(round(iy2*(1+i*sc))))),
                                    (int(round(i*tx)), int(round(i*ty))))
                        self.screen.blit(self.myfont.render(text.replace('data/Pictures/Arkiv ARDO/', ''),
                                                    1, (255,255,0)), (10, 970))
                        pygame.display.flip()
                #END ZOOM
            except:
                traceback.print_exc()  #TMP
                print 'Dir=', type(dir), dir, 'fil=', type(fil), fil
                #sys.exit()
                return
        if wait:
            t = time.time() - t0
            if web.data['intervall'] > t:
                time.sleep(web.data['intervall']-t)
        pygame.display.flip()
        if ext in self.videoExt:
            os.system('omxplayer "' + dir + '/' + fil + '"')
        return

    def run(self):
        dirList = None
        res = {}
        while True:
            if not dirList:
                #read shown dirs
                shownFiles = [line.rstrip('\n') for line in open(self.filename)]
            else:
                shownFiles = []
            dirList = dirs.genListRandom(web.data['filter'])
            if len(dirList)<1:
                dirList = dirs.genListRandom()
                web.data['filter'] = None
                #print('No dirs found with filter %s- reset to all' % (web.data['filter'],) )
            print('Ant dirs=', len(dirList))
            for r in dirList:
                if web.data['query']:
                    #h = urllib2.urlopen("http://aaphoto/genLists.php?query=%s&cond=%s" % (web.data['query'].encode('utf-8'), web.data['cond']))
                    url = "http://aaphoto/genLists.php?query=%s&cond=%s" % (quote_plus(web.data['query'].encode('utf8')), web.data['cond'])
                    if web.data['date1']: url += "&date1=%s" % (web.data['date1'])
                    if web.data['date2']: url += "&date2=%s" % (web.data['date2'])
                    h = urllib2.urlopen(url)
                    res = json.loads(h.read())
                    files = res.keys()
                    h.close()
                    print('Q=',web.data['query'],'Ant files=',len(files))
                    #self.label = self.myfont.render(web.data['query'], 1, (0,255,0))  #use tag instead of directory
                    self.label = web.data['query']  #use tag instead of directory
                    r = ''
                else:
                    #test if r already shown
                    if r in shownFiles: continue
                    with open(self.filename,'ab') as f:
                        f.write(r + "\n")
                    shownFiles.append(r)
                    files = dirs.allDirs[r]
                    web.data['files'] = files
                    print('Dir=', r, 'Ant files=',len(files))
                    lstr = r.replace(startdir, '').decode('utf-8').encode('latin-1')
                    #self.label = self.myfont.render(lstr, 1, (0,255,0))
                    self.label = lstr
                for f in files:
                    f = f.lstrip('/')
                    #print 'F=', f
                    if web.data['command']:
                        #commands handled below
                        break
                    while web.data['pause']:
                        #stop auto mode and manually show files
                        if web.data['file']:
                            self.show(r, web.data['file'])
                            web.data['file'] = None
                        time.sleep(1)
                    #resume auto mode
                    self.show(r, f, True, res.get('/'+f))  #COORD res[f] or None
                #handle commands
                if web.data['command'] == 'NextDir':
                    web.data['command'] = None
                    web.data['query'] = None
                elif web.data['command'] == 'Exit':
                    pygame.quit()
                    sys.exit()
                elif web.data['command'] == 'showTag':
                    web.data['command'] = None
                    #print 'showTag', web.data['query']
                    break
                elif web.data['command'] == 'Restart':
                    web.data['command'] = None
                    web.data['query'] = None
                    #print 'Restart', web.data['filter']
                    break
                elif web.data['command'] == 'rescan':
                    web.data['command'] = None
                    web.data['query'] = None
                    #dirs.rescan(comLine[2:]).rstrip("\n") #??
                    print('rescan - not implemented yet')
                    break
        # make sure to call pygame.quit() if using the framebuffer to get back to your terminal
        pygame.quit()

class index:
    def GET(self):
        return render.index(sorted(dirs.dirHier['Arkiv ARDO'].keys()), dirs.tagList)
    
class Exit:
    def GET(self):
        web.data['command'] = 'Exit'
        return render.index(sorted(dirs.dirHier['Arkiv ARDO'].keys()), dirs.tagList)
    
class nextdir:
    def GET(self):
        web.data['command'] = 'NextDir'
        return render.index(sorted(dirs.dirHier['Arkiv ARDO'].keys()), dirs.tagList)
    
class intervall:
    def GET(self):
        t = web.input()
        web.data['intervall'] = int(t.tid)
        return render.index(sorted(dirs.dirHier['Arkiv ARDO'].keys()), dirs.tagList)
    
class restart:
    def GET(self):
        t = web.input()
        web.data['filter'] = t.filter
        web.data['command'] = 'Restart'
        return render.index(sorted(dirs.dirHier['Arkiv ARDO'].keys()), dirs.tagList)
    
class level2:
    def GET(self):
        t = web.input()
        return render.level2(sorted(dirs.dirHier['Arkiv ARDO'][t.l1]))
    
class pause:
    def GET(self):
        web.data['pause'] = True
        return render.files(web.data['files'])
    
class showFile:
    def GET(self):
        t = web.input()
        web.data['file'] = t.f.decode('utf-8').encode('latin-1')
        return ''
    
class showTag:
    def GET(self):
        t = web.input()
        #web.data['query'] = t.q.decode('utf-8').encode('latin-1')
        #web.data['query'] = t.q
        q = []
        for (key, val) in t.iteritems():
            if key in ('mode', 'cond', 'date1', 'date2'):
                web.data[key] = val
                continue
            q.append("'" + key.decode('utf-8') + "'")
        web.data['query'] = ','.join(q)
        web.data['command'] = 'showTag'
        return render.index(sorted(dirs.dirHier['Arkiv ARDO'].keys()), dirs.tagList)
    
class cont:
    def GET(self):
        web.data['pause'] = False
        return render.index(sorted(dirs.dirHier['Arkiv ARDO'].keys()), dirs.tagList)

class status:
    def GET(self):
        html = ''
        for stat in web.data.keys():
            if stat == 'files': continue
            elif stat == 'intervall':
                html += "%s = %d <br>\n" % (stat, web.data[stat])
            else:
                html += "%s = %s <br>\n" % (stat, web.data[stat])
        return html

class mediatype:
    def GET(self):
        t = web.input()
        web.data['mediatype'] = t.mediatype
        return render.index(sorted(dirs.dirHier['Arkiv ARDO'].keys()), dirs.tagList)


if __name__ == "__main__":
    ######## Web Ctrl UI
    render = web.template.render('templates/')
    urls = (
        '/', 'index',
        '/Exit', 'Exit',
        '/nextdir', 'nextdir',
        '/intervall', 'intervall',
        '/mediatype?', 'mediatype',
        '/restart?', 'restart',
        '/level2?', 'level2',
        '/pause', 'pause',
        '/showFile?', 'showFile',
        '/showTag?', 'showTag',
        '/cont', 'cont',
        '/status', 'status'
    )
    #global data
    web.data = {'intervall': 10,
                'mediatype': 'both',
                'filter': None,
                'command': None,
                'file': None,
                'pause': False,
                'zoom': True,
                'query': None, 'cond': 'OR', 'date1': '', 'date2': '' } 
    startdir = '/data/Pictures/Arkiv ARDO/'
    #startdir = '/data/Pictures/Arkiv ARDO/2002/'
    dirs = imgDirectories(startdir)
    print 'dirs scanned and initialized',  startdir
    app = web.application(urls, globals())
    thread = dataThread()
    thread.start()
    app.run()
