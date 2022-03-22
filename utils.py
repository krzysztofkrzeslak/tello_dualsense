def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    # Convert the left range into a 0-1 range (float)
    valueScaled = float(abs(value) - leftMin) / float(leftSpan)
    # Convert the 0-1 range into a value in the right range.
    if(value<0):
       return -(int(rightMin + (valueScaled * rightSpan)))
    else:
       return int(rightMin + (valueScaled * rightSpan))