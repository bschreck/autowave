#!/usr/local/bin/python
import sys, getopt
import wave

def main(argv):
    inputFile = ''
    outputFile = ''
    period = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:p:",["ifile=","ofile=","period="])
    except getopt.GetoptError:
        print 'usage: automate_pan.py -i <inputfile> -o <outputfile> -p',\
        '<period>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'usage: automate_pan.py -i <inputfile> -o <outputfile> -p',\
            '<period>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputFile = arg
        elif opt in ("-o", "--ofile"):
            outputFile = arg
        elif opt in ("-p", "--period"):
            period = arg

    if not inputFile or inputFile[-4:] != '.wav':
        print "must provide a valid .wav input file"
        sys.exit(2)
    if not outputFile:
        print "must provide a valid output file"
        sys.exit(2)
    if outputFile[-4:] != '.wav':
        outputFile += '.wav'
    print 'Input file = ', inputFile
    print 'Output file = ', outputFile
    if period:
        try:
            period = int(period)
        except:
            print "Period argument must be an integer"
            sys.exit(2)
    else:
        period = 7
    print 'Period = ', period

    wOld = wave.open(inputFile, 'r')
    wNew = wave.open(outputFile, 'w')

    width = wOld.getsampwidth()
    print "Sample Width: ", width
    channels = wOld.getnchannels()
    print "Number of Channels: ", channels

    wNew.setframerate(wOld.getframerate())
    wNew.setnchannels(wOld.getnchannels())
    wNew.setsampwidth(wOld.getsampwidth())
    wNew.setnframes(wOld.getnframes())

    period = 7 # seconds
    print "Period: ", period
    framesInPeriod = wOld.getframerate() * period
    oneSecond = wOld.getframerate()

    print 'Number of Frames:', wOld.getnframes()

    # leftRamp increments the multiplier
    leftRamp = -1./framesInPeriod
    # leftMultiplier scales the data
    leftMultiplier = 0


    print "working..."
    for i in range(wOld.getnframes()):
        # change from positive left slope to negative
        if i % framesInPeriod == 0:
            leftRamp = -leftRamp

        oldFrame = wOld.readframes(1)

        # get data from frame, stored as
        # 2's complement little endian hex characters
        newFrameIntLeft = ord(oldFrame[0]) + ord(oldFrame[1])*256
        # for 2's complement:
        if newFrameIntLeft >= 32768:
            newFrameIntLeft -= 65536
            newFrameIntLeft = int(round(newFrameIntLeft * leftMultiplier))
            newFrameIntLeft += 65536
        else:
            newFrameIntLeft = int(round(newFrameIntLeft * leftMultiplier))

        newFrameIntRight = ord(oldFrame[2]) + ord(oldFrame[3])*256
        if newFrameIntRight >= 32768:
            newFrameIntRight -= 65536
            newFrameIntRight = int(round(newFrameIntRight * (1-leftMultiplier)))
            newFrameIntRight += 65536
        else:
            newFrameIntRight = int(round(newFrameIntRight * (1-leftMultiplier)))

        # In case rounding errors produce slight clipping
        if newFrameIntLeft >= 65536:
            newFrameIntLeft = 65535
        if newFrameIntRight >= 65536:
            newFrameIntRight = 65535

        # convert data back to string format
        newFrame = chr(newFrameIntLeft % 256) + chr(newFrameIntLeft / 256) \
                 + chr(newFrameIntRight % 256) + chr(newFrameIntRight / 256)
        # write data
        wNew.writeframes(newFrame)

        # increment multiplier
        leftMultiplier += leftRamp

        # In case of rounding errors
        if leftMultiplier > 1:
            leftMultiplier = 1
        if leftMultiplier < 0:
            leftMultiplier = 0

    wOld.close()
    wNew.close()

if __name__ == "__main__":
    main(sys.argv[1:])
