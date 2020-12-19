from sys import argv
from PIL import Image, ImageDraw, ImageStat
from random import randint
from math import sqrt, sin, cos, pi
from functools import reduce


def get_pins_circle(total_pins, size):
    radius = min(size[0], size[1]) / 2 - 1
    origin = (size[0] / 2, size[1] / 2)
    pins = []
    for i in range(total_pins):
        pins.append((int(radius * cos(i * 2 * pi / total_pins) + origin[0]),
                     int(radius * sin(i * 2 * pi / total_pins) + origin[1])))

    return pins


def get_pins_square(pins_per_side, size):
    pins = []
    dx = size[0] / pins_per_side
    dy = size[1] / pins_per_side
    for i in range(pins_per_side):
        pins.append((int(dx * (i + 0.5)), 0))
        pins.append((int(dx * (i + 0.5)), size[1]-1))
        pins.append((0, int(dy * (i + 0.5))))
        pins.append((size[0]-1, int(dy * (i + 0.5))))

    return pins


def dist(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return sqrt(dx**2 + dy**2)


def pos_equals(pos0, pos1): return pos0[0] == pos1[0] and pos0[1] == pos1[1]


def avg_brightness(img, pos0, pos1):
    mask = Image.new('1', img.size)
    ImageDraw.Draw(mask).line([pos0, pos1], fill=1)
    return sum(ImageStat.Stat(img, mask).mean)


def find_next_pin(src_img, pins, curr_pin, taken):
    best_pin = None
    best_dist = src_img.size[0] + src_img.size[1]
    best_bright = best_dist * 255*3
    for i, pin in enumerate(pins):
        if pos_equals(pin, pins[curr_pin]) or (i, curr_pin) in taken:
            continue
        curr_bright = avg_brightness(src_img, pin, pins[curr_pin])
        curr_dist = dist(pin, pins[curr_pin])
        if curr_bright < best_bright or (curr_bright == best_bright and curr_dist > best_dist):
            best_bright = curr_bright
            best_pin = i
            best_dist = curr_dist

        if best_pin == None:
            print(curr_pin)
    return best_pin


def total_brightness(img):
    return sum(ImageStat.Stat(img).mean)


def print_usage(index):
    # there cannot be an error with index 0, that's the python file
    if(index):
        args = ' '.join(map(str, argv))
        print('error with {} argument of '.format(index+1) + args)
    print(
        'Usage: {} <inputpath> <outputpath> [-o <image output file>] [-t <minimum brightness tollerance factor>] [-p <# pins>] [-s]'.format(argv[0]))


def parse_opts():
    if len(argv) == 1:
        print_usage(None)
        return None

    # records valid options and whether they have a parameter
    valid_opts = {"-o": True, "-t": True, "-p": True, "-s": False}
    # value to be returned. A dictionary with the options and their values. These are the default values
    opts = {'-o': None, '-t': '0.73', '-p': '74', '-s': False}

    # records how many arguments have been passed without a specified option (0 <=> input, 1 <=> output, 2+ <=> error)
    file = 0

    inputs = enumerate(argv[1:])
    for i, arg in inputs:
        if arg in valid_opts:
            if valid_opts[arg]:
                parameter = next(inputs)
                opts[arg] = parameter[1]
            else:
                opts[arg] = True
        else:
            if file == 0:
                opts['input'] = arg
            elif file == 1:
                opts['output'] = arg
            else:
                print_usage(i)
                return None
            file += 1
    if file != 2:
        print("missing input and/or output file")
        print_usage(None)
        return None
    return opts


if __name__ == '__main__':
    opts = parse_opts()

    DEFAULT_SIZE = (1000, 1000)
    TOTAL_PINS = int(opts['-p'])
    TOLLERANCE = float(opts['-t'])

    src_img = Image.open(opts['input']).resize(DEFAULT_SIZE)
    size = src_img.size
    out_img = Image.new('RGB', size, color=(255, 255, 255))

    pins = []
    if opts['-s']:
        pins = get_pins_square(int(TOTAL_PINS / 4), size)
    else:
        pins = get_pins_circle(TOTAL_PINS, size)

    times_used = [0] * len(pins)

    print(list(enumerate(pins)), sep='\n')

    midpt = (int(size[0] / 2), int(size[1] / 2))

    taken = set()

    target_brightness = total_brightness(src_img)

    src_draw = ImageDraw.Draw(src_img)
    out_draw = ImageDraw.Draw(out_img)
    with open(opts['output'], 'w') as f:
        curr_pin = randint(0, len(pins) - 1)
        prev_pin = curr_pin
        curr_b = 255*3
        i = 0
        while curr_pin != None and TOLLERANCE * curr_b > target_brightness:
            times_used[curr_pin] += 1
            src_draw.line(pins[prev_pin] + pins[curr_pin],
                          fill=(255, 255, 255))
            out_draw.line(pins[prev_pin] + pins[curr_pin], fill=(0, 0, 0))
            taken.add((prev_pin, curr_pin))
            taken.add((curr_pin, prev_pin))
            curr_b = total_brightness(out_img)
            print(i, '{:.0f} / {:.0f} = {:.3f}, target {:.3f}'.format(
                target_brightness, curr_b, target_brightness / curr_b, TOLLERANCE))
            i += 1
            print((curr_pin, pins[curr_pin]), file=f)
            prev_pin = curr_pin
            curr_pin = find_next_pin(src_img, pins, curr_pin, taken)

    #print(list(reduce(lambda x, y: max(x, y), times_used)))
    print(max(times_used), 'is the most one pin is used')
    out_img.show()
    if opts['-o']:
        out_img.save(opts['-o'])
