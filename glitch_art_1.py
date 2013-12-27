#!/usr/local/bin/python
import sys, getopt
import wave
from scipy import signal
from scipy.fftpack import fft
import numpy as np

def main(argv):
    inputFile = ''
    outputFile = ''
    modFile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:m:",["ifile=","ofile=","mfile="])
    except getopt.GetoptError:
        print 'usage: automate_pan.py -i <inputfile> -o <outputfile> -m'+\
        '<modfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'usage: automate_pan.py -i <inputfile> -o <outputfile>'+\
            '<modfile>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputFile = arg
        elif opt in ("-o", "--ofile"):
            outputFile = arg
        elif opt in ("-m", "--mfile"):
            modFile = arg

    if not inputFile or inputFile[-4:] != '.wav':
        print "must provide a valid .wav input file"
        sys.exit(2)
    if not outputFile:
        print "must provide a valid output file"
        sys.exit(2)
    if not modFile or modFile[-4:] != '.wav':
        print "must provide a valid .wav mod file"
        sys.exit(2)
    if outputFile[-4:] != '.wav':
        outputFile += '.wav'
    print 'Input file = ', inputFile
    print 'Output file = ', outputFile
    print 'Mod file = ', modFile


    wOld = wave.open(inputFile, 'r')
    wNew = wave.open(outputFile, 'w')
    wMod = wave.open(modFile, 'r')

    width = wOld.getsampwidth()
    print "Sample Width: ", width
    channels = wOld.getnchannels()
    print "Number of Channels: ", channels

    #wNew.setframerate(wOld.getframerate())
    #wNew.setnchannels(wOld.getnchannels())
    #wNew.setsampwidth(wOld.getsampwidth())
    #wNew.setnframes(wOld.getnframes())
    wNew.setframerate(wMod.getframerate())
    wNew.setnchannels(wMod.getnchannels())
    wNew.setsampwidth(wMod.getsampwidth())
    wNew.setnframes(wMod.getnframes()/4)

# set framerate of mod file to same as inputFile
# alter magnitude by a low-pass filter from inputFile, and decrease to like 0.1 of original
# add high frequencies of inputFile by this new version of modFile

# New idea:
# just take "we are part of this universe"
# somehow alter original song with that

    modArray = []
    for i in range(wMod.getnframes()):
        oldFrame = wMod.readframes(1)
        frameLeft = ord(oldFrame[0]) + ord(oldFrame[1])*256
        if frameLeft >= 32768:
            frameLeft -= 65536
        frameRight = ord(oldFrame[2]) + ord(oldFrame[3])*256
        if frameRight >= 32768:
            frameRight -= 65536
        modArray.append([frameLeft, frameRight])


    def lowPass(samp_rate, cutoff, inputArray):

        # design filter
        norm_pass = cutoff/(samp_rate/2)
        norm_stop = 1.5*norm_pass
        (N, Wn) = signal.buttord(wp=norm_pass, ws=norm_stop, gpass=2, gstop=30, analog=0)
        (b, a) = signal.butter(N, Wn, btype='low', analog=0, output='ba')

        # filtered output
        #zi = signal.lfiltic(b, a, x[0:5], x[0:5])
        #(y, zi) = signal.lfilter(b, a, x, zi=zi)
        return signal.lfilter(b, a, inputArray, axis=0)


    #each frequency in cutoff must be between 0 and nyq
    modLowPass = lowPass(2000, 60., modArray)
    fftMod = fft(modLowPass, axis = 1)
    smallModLowPass = np.multiply(fftMod, 0.05)
    modLength = wMod.getnframes()

    for i in range(wOld.getnframes()):
        oldFrame = wOld.readframes(1)
        frameLeft = ord(oldFrame[0]) + ord(oldFrame[1])*256
        if frameLeft >= 32768:
            frameLeft -= 65536
            newFrameLeft = int(round(frameLeft*.5 + smallModLowPass[i%modLength][0]))

            frameLeft = newFrameLeft + 65536
        else:
            newFrameLeft = int(round(frameLeft*.5 + smallModLowPass[i%modLength][0]))

            frameLeft = newFrameLeft


        frameRight = ord(oldFrame[0]) + ord(oldFrame[1])*256
        if frameRight >= 32768:
            frameRight -= 65536
            frameRight = int(round(frameRight*.5 + smallModLowPass[i%modLength][1]))
            frameRight += 65536
        else:
            frameRight = int(round(frameRight*.5 + smallModLowPass[i%modLength][1]))

        # In case rounding errors produce slight clipping
        if frameLeft >= 65536:
            frameLeft = 65535
            #print frameLeft
        if frameLeft < 0:
            frameLeft = 0
            #print frameLeft
        if frameRight >= 65536:
            frameRight = 65535
            #print frameRight
        if frameRight < 0:
            frameRight = 0
            #print frameRight

        # convert data back to string format
        toWrite = chr(frameLeft % 256) + chr(frameLeft / 256) \
                 + chr(frameRight % 256) + chr(frameRight / 256)
        # write data
        wNew.writeframes(toWrite)

    wMod.close()
    wOld.close()
    wNew.close()


if __name__ == "__main__":
    main(sys.argv[1:])
