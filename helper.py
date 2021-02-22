import numpy as np
import pandas as pd
from math import pi, tau
from typing import Tuple

from datetime import datetime, timedelta
import pytz
import timezonefinder
import suncalc

from colorsys import hls_to_rgb
from PIL import Image


# generate initial 1d array of UTC datetime objects
def time_arr(year: int, lon: float, lat: float, use_dst: bool = True) -> np.ndarray:
    # determine timezone based on lon, lat
    tz_str = timezonefinder.TimezoneFinder().certain_timezone_at(lat=lat, lng=lon)
    tz = pytz.timezone(tz_str)

    # generate local start and end times
    # localize with derived time zone
    start_time = pd.to_datetime(datetime(year, 1, 1))
    end_time = pd.to_datetime(datetime(year, 12, 31, 23, 59))

    if use_dst:
        # generate times
        times = pd.date_range(start_time, end_time, freq='min') \
            .tz_localize(tz, ambiguous=True, nonexistent=timedelta(days=1))
    else:
        # convert to UTC to capture offset
        start_time = start_time.tz_localize(tz).tz_convert('UTC')
        end_time = end_time.tz_localize(tz).tz_convert('UTC')

        # generate times
        times = pd.date_range(start_time, end_time, freq='min')

    # convert to UTC then python datetime objects in numpy array
    return times.tz_convert('UTC').to_pydatetime()


# get azimuth and altitude from dates and location
def sun_positions(arr_utc: np.ndarray, lon: float, lat: float) -> Tuple[np.ndarray, np.ndarray]:
    sc = suncalc.get_position(arr_utc, lon, lat)
    return sc['azimuth'], sc['altitude']


# azimuth, altitude to color
def get_colors(azimuths: np.ndarray, altitudes: np.ndarray, sunrise_jump=0.0, hue_shift=0.0) \
        -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # ranges from 0 (no jump) to 1 (day is all white, night all black)
    assert 0 <= sunrise_jump <= 1, "sunrise_jump must be between 0 and 1 inclusive"

    # can be any float, but values outside the range [0, 1) are redundant
    # shifts all hues in the r -> g -> b -> r direction
    assert isinstance(hue_shift, float), "hue_shift must be a float"

    # yes, this could be simplified, and no, don't try to do it please.
    altitude_scaled = (altitudes / pi) * 2  # range [-1, 1]
    altitude_scaled *= 1 - sunrise_jump
    idx_alt_pos = altitude_scaled >= 0
    idx_alt_neg = altitude_scaled < 0
    altitude_scaled[idx_alt_pos] += sunrise_jump
    altitude_scaled[idx_alt_neg] -= sunrise_jump

    hue = ((azimuths / tau) + 0.5 + hue_shift) % 1  # range [0, 1]
    lightness = altitude_scaled / 2 + 0.5  # range [0, 1]
    saturation = np.ones(hue.shape)  # range [1, 1]

    r, g, b = np.vectorize(hls_to_rgb)(hue, lightness, saturation)

    r = np.round(255 * r)
    g = np.round(255 * g)
    b = np.round(255 * b)

    return r, g, b


# stack RGB elements into 3d pixel array
def stack_rgb(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    width = int(len(r) / 1440)  # in case of leap year
    new = np.empty((1440, width, 3), dtype=np.uint8)
    new[:, :, 0] = r.reshape((-1, 1440)).T
    new[:, :, 1] = g.reshape((-1, 1440)).T
    new[:, :, 2] = b.reshape((-1, 1440)).T
    return new


# generate PNG using pixel data
def gen_png(rgb_arr: np.ndarray, width_px: int, height_px: int, file_name: str) -> None:
    if file_name[-4:] != '.png':
        file_name = file_name + '.png'
    Image.fromarray(rgb_arr, mode="RGB") \
        .resize((rgb_arr.shape[1], height_px), Image.BOX) \
        .resize((width_px, height_px), Image.NEAREST) \
        .save(file_name)

def gen_png_to_stream(rgb_arr: np.ndarray, width_px: int, height_px: int, fp) -> None:
    Image.fromarray(rgb_arr, mode="RGB") \
        .resize((rgb_arr.shape[1], height_px), Image.BOX) \
        .resize((width_px, height_px), Image.NEAREST) \
        .save(fp, format='png')