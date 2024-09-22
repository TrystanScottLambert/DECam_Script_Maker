"""
Script to make DECAM observational script 
"""
import json
from datetime import timedelta
from typing import TextIO

import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

DEC_OFFSET = 5/60  # 5 arcminute offset to play in center of field
DITHER_OFFSET = 120/3600 # 120 arcsecond dithers +-

def prettify_sky_coords(coords: SkyCoord) -> str:
    """Removes the letters in coordinate strings and replaces them with ':'"""
    string_with_letters = coords.to_string('hmsdms')
    letters = ['h', 'm', 'd']
    for letter in letters:
        string_with_letters = string_with_letters.replace(letter,':')

    string_with_no_letters = string_with_letters.replace('s','')
    return string_with_no_letters

class ExposureSequence:
    """Main class for storing the exposure sequence variables."""
    def __init__(
            self, ra: str, dec: str, filter_choice: str, exp_time: int, number_of_exposures: int
            ) -> None:
        self.ra = (
            int(ra.split(':')[0]) + \
            int(ra.split(':')[1])/60 + \
            float(ra.split(':')[2])/3600)*(360/24)

        if dec[0] == '-':
            self.dec = int(
                dec.split(':')[0]) - int(dec.split(':')[1])/60 - float(dec.split(':')[2])/3600
        else:
            self.dec = int(
                dec.split(':')[0]) + int(dec.split(':')[1])/60 + float(dec.split(':')[2])/3600

        self.exp_time = exp_time
        self.filter_choice = filter_choice
        self.number_exposures = number_of_exposures

    @property
    def dithered_positions(self) -> tuple[list[float], list[float]]:
        """Random dithered positions"""
        ra_dithers = np.random.random(self.number_exposures)*2*DITHER_OFFSET - DITHER_OFFSET
        dec_dithers = np.random.random(self.number_exposures)*2*DITHER_OFFSET - DITHER_OFFSET
        dithered_ra = self.ra + ra_dithers
        dithered_dec = self.dec + dec_dithers + DEC_OFFSET
        return dithered_ra, dithered_dec

    def add_sequence(self, file: TextIO, include_end_comma: bool = True)  -> None:
        """Writes a sequence to a file of exposures."""
        ra_positions, dec_positions = self.dithered_positions
        for i, pos in enumerate(zip(ra_positions, dec_positions)):
            c = SkyCoord(ra = pos[0]*u.deg, dec = pos[1]*u.deg)
            position_to_write = prettify_sky_coords(c)
            ra_to_write = position_to_write.split(' ')[0]
            dec_to_write = position_to_write.split(' ')[1]
            file.write(' { \n')
            file.write('  "expType": "object", \n')
            file.write('  "object": "VIK_J2348-3054", \n')
            file.write(f'  "RA": "{ra_to_write}", \n')
            file.write(f'  "dec": "{dec_to_write}", \n')
            file.write(f'  "filter": "{self.filter_choice}", \n')
            file.write(f'  "expTime": {self.exp_time} \n')
            if i == self.number_exposures-1 and include_end_comma is False:
                file.write(' } \n')
            else:
                file.write(' }, \n')

def calculate_total_time(script_name: str) -> float:
    """Determines total observational time."""
    with open(script_name, encoding='utf8') as file:
        data = json.load(file)
        times = [val['expTime'] for val in data]
    return int(np.sum(times) + 28*len(times))

def construct_script(file_name: str, *args) -> None:
    """Builds the current observing script."""
    with open(file_name, 'w', encoding='utf8') as file:
        file.write('[ \n')
        for i, arg in enumerate(args):
            if i == len(args)-1:
                arg.add_sequence(file, include_end_comma=False)
            else:
                arg.add_sequence(file)
        file.write('] \n')

    print(f'Total Time of Script ~ {timedelta(seconds = calculate_total_time(file_name))}')

if __name__ == '__main__':
    RA =  '23:48:33.34'
    DEC = '-30:54:10.0'
    NarrowSequence_1  = ExposureSequence(RA, DEC, 'Y', 200, 30)
    #NarrowSequence_1  = ExposureSequence(RA,Dec,'i',200,10
    #,BroadSequence_1,NarrowSequence_2,BroadSequence_2)
    construct_script('y_two_hours_6.json', NarrowSequence_1)
