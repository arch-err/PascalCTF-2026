# Very Simple Framer

## Description
> *I decided to make a simple framer application, obviously with the help of my dear friend, you really think I would write that stuff?*

**Files:** [output.jpg](./orig/output.jpg), [chal.py](./orig/chal.py)

## Solution
**TL;DR**: Decode binary data from 1-pixel image border (black=0, white=1)
1. Analyze the Python script `chal.py` which encodes a message into the border pixels of an image
2. The border is traversed clockwise: top row L→R, right column T→B, bottom row R→L, left column B→T
3. Each character is converted to 8-bit binary, black pixels = '0', white pixels = '1'
4. Write a decoder script that extracts pixel values from the border and converts back to ASCII

### Flag
> `pascalCTF{Wh41t_wh0_4r3_7h0s3_9uy5???}`
