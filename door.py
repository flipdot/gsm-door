import serial
import pygame
import pygame.gfxdraw
from pygame.locals import *
import time
import os
import RPi.GPIO as GPIO
#import board
 
from rpi_ws281x import PixelStrip, Color
import argparse

# LED strip configuration:
# https://dordnung.de/raspberrypi-ledstrip/ws2812
LED_COUNT = 5        # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

# Create NeoPixel object with appropriate configuration.
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
# Intialize the library (must be called once before other functions).
strip.begin()
    
bereit = 0
anruf = 1
zugang = 2
verweigert = 3
warte = 4
    
strip.setPixelColorRGB(bereit, 255, 100, 0)
strip.show()


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

## todo: set usb adapter to fixed enumeration
try:
    ser = serial.Serial('/dev/ttyAMA0', 19200)
except:
    print "wrong USB port"
    
#-----------------------------------------------------------------------------------------------------------------
# pygame related stuff
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (90, 90, 90)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

class pyscope :
    screen = None;
    
    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)
        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print 'Driver: {0} failed.'.format(driver)
                continue
            found = True
            break
        if not found:
            raise Exception('No suitable video driver found!')
        
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "Framebuffer size: %d x %d" % (size[0], size[1])
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))        
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()
                
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

# Create an instance of the PyScope class
scope = pyscope()
pygame.mouse.set_visible(False)
#clock = pygame.time.Clock()

font = pygame.font.Font("/home/pi/door/isocpeur.ttf", 75) # font for all text outputs


#-----------------------------------------------------------------------------------------------------------------
# setup used hardware ports
GPIO.setup(7, GPIO.OUT)                 # GSM Modem switch on / off
GPIO.output(7, GPIO.LOW)                # Set switch input to normal = off
GPIO.setup(4, GPIO.IN)                 # DSR output from modem to GPIO 18 input RasPi
GPIO.setup(8, GPIO.OUT)
GPIO.output(8, GPIO.HIGH)               # Relais, HIGH = off!
GPIO.setup(23, GPIO.OUT)                # 23, 24, 25: Auxiliary relais lines 
GPIO.output(23, GPIO.HIGH)
GPIO.setup(24, GPIO.OUT)
GPIO.output(24, GPIO.HIGH)
GPIO.setup(25, GPIO.OUT)
GPIO.output(25, GPIO.HIGH)


#-----------------------------------------------------------------------------------------------------------------
# function tests if one of the user phone numbers in user.txt is found in modem answer string for incoming call)
def check_credentials (string_to_test):
    access = ""
    inp = open ("/home/pi/door/user.txt","r")         # load list with username and phone number
    for line in inp.readlines():        # read every line 
        line = line[:-1]                # strip cr/lf from end of string
        if (line != ""):                # if line not empty 
            elements = line.split()     # split lines in file in name and phone number
            if elements[1] in string_to_test:
                access = elements[0]
    return access


#-----------------------------------------------------------------------------------------------------------------
# set modem in known status.
# if off, turn on
# if on, turn off, wait, turn on
def modem_start():
    if GPIO.input(4) == 0:                  # modem is inactive at start of script.

        scope.screen.fill(BLACK)            
        infotext = "Data set NOT ready"                  
        text = font.render(infotext, True, WHITE)
        scope.screen.blit(text, [10, 10])
        infotext = "Switching modem ON"    
        strip.setPixelColorRGB(bereit, 0, 255, 0)
        strip.show()

        text = font.render(infotext, True, WHITE)
        scope.screen.blit(text, [10, 90])           
        pygame.display.flip()

        GPIO.output(7, GPIO.HIGH)           # switch modem on
        time.sleep (2)
        GPIO.output(7, GPIO.LOW)
        time.sleep (6)    
        
    else:                                   # modem is actived at start of script.
        scope.screen.fill(BLACK)        
        infotext = "Data set active"                  
        text = font.render(infotext, True, WHITE)
        scope.screen.blit(text, [10, 10])
        infotext = "Switching modem OFF"           
        strip.setPixelColorRGB(bereit, 255, 0, 0)
        strip.show()

        text = font.render(infotext, True, WHITE)
        scope.screen.blit(text, [10, 90])           
        pygame.display.flip()

        GPIO.output(7, GPIO.HIGH)           # switch modem off ...
        time.sleep (2)
        GPIO.output(7, GPIO.LOW)
        time.sleep (6)        

        scope.screen.fill(BLACK)            
        infotext = "Switching modem ON"    
        strip.setPixelColorRGB(bereit, 0, 255, 0)
        strip.show()         
        text = font.render(infotext, True, WHITE)
        scope.screen.blit(text, [10, 10])
        pygame.display.flip()
        
        GPIO.output(7, GPIO.HIGH)           # ... and on again
        time.sleep (2)
        GPIO.output(7, GPIO.LOW)
        time.sleep (6)  

modem_start()                               # check two times for modem present. After power up, DSR level is faulty. Doing 2 power cycles fixes this issue
modem_start()

done = False

#-----------------------------------------------------------------------------------------------------------------
# main loop.
# using blocking input via serial with ser.readline()

while not done:
    line = ser.readline()                           # readline() is blocking!
    line = line[:-2]                                # strip cr/lf from end of string
    if (line != ""):
        strip.setPixelColorRGB(anruf, 255, 255, 190)
        strip.show()
        if "CLIP" in line:                          # check if modem answer contains "CLIP" 
            testresult = check_credentials (line)
            if (testresult != ""):                  # valid user found (check_credentials (line) returns user name if access granted)

                scope.screen.fill(BLACK)
                infotext = "Open the door for"                 
                text = font.render(infotext, True, WHITE)
                scope.screen.blit(text, [10, 10])           

                infotext = testresult 
                text = font.render(infotext, True, GREEN)
                scope.screen.blit(text, [10, 90])           
                pygame.display.flip()

                strip.setPixelColorRGB(zugang, 0, 255, 0)
                strip.show()

                GPIO.output(8, GPIO.LOW)            # activate electric door opener
                time.sleep(5)
                GPIO.output(8, GPIO.HIGH)
                modem_start()                       # shut down modem and start again
                
                strip.setPixelColorRGB(zugang, 0, 0, 0)
                strip.show()
                                
                scope.screen.fill(BLACK)
                infotext = "Delay for 30 sec."                  
                text = font.render(infotext, True, WHITE)
                scope.screen.blit(text, [10, 10])
                pygame.display.flip()

                strip.setPixelColorRGB(warte, 255, 255, 190)
                strip.show()
                                
                time.sleep(30)                    
                ser.reset_input_buffer()                

                strip.setPixelColorRGB(warte, 0, 0, 0)
                strip.show()
                    
            else:                                   # no valid user found, deny access
                scope.screen.fill(BLACK)
                infotext = "No access, dude"
                text = font.render(infotext, True, RED)
                scope.screen.blit(text, [10, 10])                      
                pygame.display.flip()
                
                strip.setPixelColorRGB(verweigert, 255, 0, 0)
                strip.show()
                                
                time.sleep(5)
                ser.reset_input_buffer() 
                modem_start()                       # shut down modem and start again

                strip.setPixelColorRGB(verweigert, 0, 0, 0)
                strip.show()
                
                strip.setPixelColorRGB(warte, 255, 255, 190)
                strip.show()
                                
                time.sleep(30)                    
                ser.reset_input_buffer()                

                strip.setPixelColorRGB(warte, 0, 0, 0)
                strip.show()
                
        strip.setPixelColorRGB(anruf, 0, 0, 0)
        strip.show()
                
    scope.screen.fill(BLACK)
    infotext = "Waiting for calls"                 
    text = font.render(infotext, True, GREEN)
    scope.screen.blit(text, [10, 10])           
    pygame.display.flip()

    for event in pygame.event.get():  # User did something
        if event.type == pygame.KEYDOWN:  # If user pressed any key
            done = True  # Flag that we are done so we exit this loop    
                        
    # clock.tick(100) # argument defines frame rate

pygame.quit()
