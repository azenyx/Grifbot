import numpy as np
import cv2
from time import sleep, process_time
import math
import ctypes
from ctypes import wintypes
import time
from win32gui import GetWindowText, GetForegroundWindow
import PySimpleGUI as sg
import configparser
from os import path
from win32api import GetSystemMetrics
import mss

logf = open("Error.log", "w")

user32 = ctypes.WinDLL('user32', use_last_error=True)

INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
KEYEVENTF_SCANCODE    = 0x0008

MAPVK_VK_TO_VSC = 0

SHIFT = 0xF
W = 0x57
A = 0x41
S = 0x53
D = 0x44
Q = 0x51


UP = 0x26
DOWN = 0x28
wintypes.ULONG_PTR = wintypes.WPARAM
POINTER = ctypes.POINTER(ctypes.c_ulong)


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))
#for mouse emulation
class MouseInput(ctypes.Structure): 
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", POINTER)]


class MouseInputField(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", MouseInputField)]
def set_pos(x, y):
    x = 1 + int(x * 65536./1920.)
    y = 1 + int(y * 65536./1080.)
    extra = ctypes.c_ulong(0)
    ii_ = MouseInputField()
    ii_.mi = MouseInput(x, y, 0, (0x0001 | 0x8000), 0, ctypes.pointer(extra))
    command = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

#End mouse spin emulation


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk,
                                                 MAPVK_VK_TO_VSC, 0)

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT))

LPINPUT = ctypes.POINTER(INPUT)
##########################
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", POINTER)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", POINTER)]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


def set_pos(x, y):
    x = 1 + int(x * 65536./1920.)
    y = 1 + int(y * 65536./1080.)
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(x, y, 0, (0x0001 | 0x8000), 0, ctypes.pointer(extra))
    command = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return args

user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (wintypes.UINT, # nInputs
                             LPINPUT,       # pInputs
                             ctypes.c_int)  # cbSize
# Functions

def PressKey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode,
                            dwFlags=KEYEVENTF_KEYUP))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def waitsec(sec):
	for i in range(sec,0,-1):
		print('Starting in: ' + str(i))
		sleep(1)

def calcdistance(x,y,x2=252,y2=318):
	distance = math.sqrt((x-x2)**2 + (y-y2)**2)
	return round(distance,2)

def findstart():
	sct = mss.mss()
	h = GetSystemMetrics(0)
	w = GetSystemMetrics(1)
	print((h,w))
	#img = sct.grab((0,int(w/2),int(h/2),w)) #THIS IS THE REASON SHIT WAS BREAKING
	img = sct.grab((0,0,int(h),w))
	img2 = np.asarray(img, dtype='uint8')
	frame = cv2.cvtColor(img2, cv2.COLOR_BGRA2BGR)
	color_mask1 = cv2.inRange(frame, np.array([0,190,210]), np.array([50,255,255]))
	yellowmask = cv2.bitwise_and(frame, frame, mask = color_mask1)
	grey = cv2.cvtColor(yellowmask, cv2.COLOR_RGB2GRAY)
	contours,_ = cv2.findContours(grey,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
	for c in contours:
		obj = cv2.boundingRect(c)
		x,y,w,h = obj
		cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
		print(x+w/2,y+h/2)
		center = (x+w/2,y+h/2)

	leftx, rightx, topy, bottomy = checkbounds(center,min(center))



	return center#, center2

def getframe(leftx=0,topy=0,rightx=GetSystemMetrics(0),bottomy=GetSystemMetrics(1)):
	sct = mss.mss()
	im = sct.grab((leftx,topy,rightx,bottomy))
	img2 = np.asarray(im, dtype='uint8')
	frame = cv2.cvtColor(img2, cv2.COLOR_BGRA2BGR)

	color_mask2 = cv2.inRange(frame, np.array([0,0,235]), np.array([75,40,255])) #red
	redmask = cv2.bitwise_and(frame, frame, mask = color_mask2)
	grey = cv2.cvtColor(redmask, cv2.COLOR_RGB2GRAY)
	return frame, grey


def getconfig():
	config = configparser.ConfigParser()
	if path.exists('config.ini'):
		print('Config File Loaded')
		config.read('config.ini')

		setup = config['def']['setup']
		attack_distance = int(config['def']['attack_distance'])
		Starting_time = int(config['def']['Starting_time'])

		if setup == 'False':
			print('Modifying Config File')
			center = str(int(findstart()))
			config['def'] = {'setup': 'True', 'center': center, 'attack_distance': str(attack_distance), 'Starting_time' : str(Starting_time), "Map_Size" : str(min(center)), "show_screen" : "True", 'forward_target_biased' : "10"}
			with open('config.ini', 'w') as configfile:
				config.write(configfile)

		config.read('config.ini')
		setup = config['def']['setup']
		center = eval(config['def']['center'])
		attack_distance = int(config['def']['attack_distance'])
		Starting_time = int(config['def']['Starting_time'])
		map_size = int(float(config['def']["Map_Size"]))
		show = config['def']["show_screen"]
		xlevel = int(config['def']['forward_target_biased'])
		print("Show Screen : " + show)
		print(map_size)
		print('MiniMap Center: ' + str(center))
		print('Attack Distance: ' + str(attack_distance))
		waitsec(Starting_time)

		return setup, center, attack_distance, Starting_time, map_size, show, xlevel
		
	else:
		print('Creating Config File')
		print('Make sure you are MOVING, when the timer ends. (Also avoid looking at yellow things)')
		waitsec(10)

		center = findstart()

		config['def'] = {'setup': 'True', 'center': str(center), 'attack_distance': '40', 'Starting_time' : '5',"Map_Size" : str(min(center)), "show_screen" : "True", 'forward_target_biased' : "10"}
		with open('config.ini', 'w') as configfile:
			config.write(configfile)

def checkbounds(center,lowest_num):
	bbx = (int(center[0] - lowest_num), int(center[0] + lowest_num))
	bby = (int(center[1] + lowest_num), int(center[1] - lowest_num))
	
	for i in bbx:
		if i > GetSystemMetrics(0):
			sub = i - GetSystemMetrics(0)
			lowest_num = lowest_num - sub
	for i in bby:
		if i > GetSystemMetrics(1):
			sub = i - GetSystemMetrics(1)
			lowest_num = lowest_num - sub
			'''
	leftx = int(center[0] - lowest_num)
	rightx = int(center[0] + lowest_num)
	topy = int(center[1] + lowest_num)
	bottomy = int(center[1] - lowest_num)'''

	leftx = int(center[0] - lowest_num)
	topy = int(center[1] + lowest_num)
	rightx = int(center[0] + lowest_num)
	bottomy = int(center[1] - lowest_num)

	return leftx, topy, rightx, bottomy






setup,center, attack_distance, Starting_time, map_size , show, xlevel = getconfig()


lowest_num = map_size
'''
leftx = int(center[0] - lowest_num)
topy = int(center[1] + lowest_num)
rightx = int(center[0] + lowest_num)
bottomy = int(center[1] - lowest_num)

'''


leftx, topy, rightx, bottomy = checkbounds(center,lowest_num)
#leftx, rightx, topy, bottomy = checkbounds(center,lowest_num)

startpos = []
ran = 1
#xlevel = 10
area = 0

frame, grey = getframe(leftx,bottomy,rightx,topy)
###########
x_pos = 0
###########
center = (int(frame.shape[0]/2),int(frame.shape[1]/2))
def SpinRight(x_pos):
    while len(contours) < 1:
        set_pos(x_pos,1000)
        x_pos += 1
        if len(contours) > 1:
            break
def SpinLeft(x_pos):
    while len(contours) > 1:
        set_pos(x_pos,1000)
        x_pos -= 1


while True:
    PressKey(SHIFT)
while GetWindowText(GetForegroundWindow()) == "Halo: The Master Chief Collection  " or show == 'True':
	skip = False
	frame, grey = getframe(leftx,bottomy,rightx,topy)

	if any(frame[center[0]][center[1]]) == 0:
		skip = True
		print('Waiting for game')
		time.sleep(5)

	if not skip:

		contours,_ = cv2.findContours(grey,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

		w,h = 0,0
		shortx,shorty,shortw,shorth = 0,0,0,0
		index = 0
		shortest_distance = 5000
		for c in contours:
			index = index + 1
			obj = cv2.boundingRect(c)
			x,y,w,h = obj

			distance = calcdistance(x,y,center[0],center[1])
			if distance < shortest_distance:
				shortest_distance = distance
				shortx,shorty,shortw,shorth = obj
			else:
				cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
			cv2.putText(frame, str(index) + '. Distance: ' + str(distance),(x,y), cv2.FONT_HERSHEY_COMPLEX_SMALL,.5,(255, 255, 255))
		cv2.rectangle(frame,(shortx,shorty),(shortx+shortw,shorty+shorth),(0,255,255),2)
		cv2.line(frame,(center[0],center[1]+500),(center[0],center[1]-500),(255,0,0))
		cv2.line(frame,(center[0]+500,center[1]),(center[0]-500,center[1]),(255,0,0))
		cv2.line(frame,(center[0]+500,center[1]+xlevel),(center[0]-500,center[1]+xlevel),(0,0,255))


		try:
			if shortest_distance < attack_distance:
				ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
				time.sleep(.5)
				ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
		except:
			print('First-Time Startup: Complete')
			print('[!] Restart Script [!]')
			sleep(3)
			
		if len(contours) < 1:
                    
		    PressKey(W)
		    PressKey(SHIFT)
		    ReleaseKey(A)
		    ReleaseKey(D)
		    ReleaseKey(S)
		else:
			if shortx+w/2 > center[0]:
				#ReleaseKey(A)
				#PressKey(D)
                                SpinRight(x_pos)
			elif shortx+w/2 < center[0]:
				#ReleaseKey(D)
				#PressKey(A)
                                SpinLeft(x_pos)
			if shorty+h/2 > center[1] + xlevel:
				ReleaseKey(W)
				PressKey(S)
			elif shorty+h/2 < center[1] + xlevel:
				ReleaseKey(S)
				PressKey(W)
		if show == "True":
			cv2.imshow("Halo_Reach_Griff_Bot",frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

cv2.destroyAllWindows()
print('[!] Done, Closing Window')

