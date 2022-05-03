# Taken from python notebook provided by Prof. Ian Foster

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

import matplotlib.pyplot as plt
import matplotlib.patches as patches

import random

def construct_color(r, g, b):
    return sRGBColor(r, g, b)

def show_colors(colors):
    show_colors_at_width(0.5, colors)

def show_colors_at_width(width, colors):
    num_colors = len(colors)
    size = width/num_colors
    fig, ax = plt.subplots(figsize=(num_colors*width,width))
    ax.plot([0,width], [0,0.2*width], color='w', alpha=0)
    ax.set_xlim([0,width])
    ax.set_ylim([0,size])
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.box(False)

    for c, i in zip(colors, range(num_colors)):
        ax.add_patch( patches.Rectangle((i*size, 0),   size, size, facecolor = c.get_rgb_hex()) )
    plt.show()

def combine_colors(color1, f1, color2, f2, color3, f3):
    (r1, g1, b1) = color1.get_value_tuple()
    (r2, g2, b2) = color2.get_value_tuple()
    (r3, g3, b3) = color3.get_value_tuple()
    new_color = sRGBColor(r1*f1 + r2*f2 + r3*f3, g1*f1 + g2*f2 + g3*f3, b1*f1 + b2*f2 + b3*f3)
    return new_color

def color_diff(color1_rgb, color2_rgb):
    color1_lab = convert_color(color1_rgb, LabColor)
    color2_lab = convert_color(color2_rgb, LabColor)
    delta_e = delta_e_cie2000(color1_lab, color2_lab)
    return(delta_e)

def random_color():
    color = sRGBColor(random.random(), random.random(), random.random())
    return(color)
