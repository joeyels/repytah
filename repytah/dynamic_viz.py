#Import mido for midi file playing capabilities
import mido
#Import time to correctly space out midi messages 
import time

import numpy as np

from .example import load_ex_data, csv_to_aligned_hierarchies
from .utilities import create_sdm, find_initial_repeats
from .search import find_complete_list
from .transform import remove_overlaps

#sets up repytah, code mostly borrowed from the repytah quicksetup docs
#returns the list of repeats with no overlaps 
def setup():
    file_in = load_ex_data('../repytah/data/mazurka30-1.csv').to_numpy()
    file_out = "hierarchical_out_file.mat"
    num_fv_per_shingle = 12
    thresh = 0.02
    csv_to_aligned_hierarchies(file_in, file_out, num_fv_per_shingle, thresh, False)

    # Load the input file
    file_in = load_ex_data('../repytah/data/mazurka30-1.csv').to_numpy()
    fv_mat = file_in

    # Number of feature vectors per shingle
    num_fv_per_shingle = 12

    # Create the self-dissimilarity matrix
    self_dissim_mat = create_sdm(fv_mat, num_fv_per_shingle)

    song_length = self_dissim_mat.shape[0]
    thresh = 0.02

    # Threshold the SDM to produce a binary matrix
    thresh_dist_mat = (self_dissim_mat <= thresh)

    all_lst = find_initial_repeats(thresh_dist_mat, np.arange(1, song_length + 1), 0)
    complete_lst = find_complete_list(all_lst, song_length)

    # Each row is a different pair of repeats 
    # Column 0 is the start beat of the first instance, column 1 is the end beat of the first instance 
    # Column 2 and 3 are the same for the second instance
    lst_no_overlaps = remove_overlaps(complete_lst, song_length)[0]
    return lst_no_overlaps
    # below line is currently useless, this builds the visualizations (mat_no_overlaps, key_no_overlaps are built by remove_overlaps, 1:3)
    # output_tuple = hierarchical_structure(mat_no_overlaps, key_no_overlaps, song_length, vis=False)
 

#currently unused helper method, just the reverse math of beats2second
def second2beat(time, ticks_per_beat, tempo):
    ticks = mido.second2tick(time,ticks_per_beat, tempo)
    beat_num = ticks/ticks_per_beat
    return beat_num

# Given a beat number, return corresponding second in midi file
# The math is basically just unit conversion for why this works
def beats2second(beat, ticks_per_beat, tempo):
    tick = beat*ticks_per_beat
    return mido.tick2second(tick, ticks_per_beat, tempo)


# Code taken from a mido discussion, looks for a set_tempo msg in the file and returns tempo
def get_tempo(midi_file):
    for track in midi_file.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    return msg.tempo

# Current driver method for midi code, sets up a port and reads in the midi file, then plays 2 matching segments
def midi_player():
    #sets up port through garageband, currently IAC Driver Bus 1 is the default port on mac
    #to set up on a mac, follow the steps in the answer here: https://stackoverflow.com/questions/40498625/outputting-midi-sound-from-python-mido-library-on-mac
    outport = mido.open_output('IAC Driver Bus 1')
    #reads in midi file
    mid = mido.MidiFile('repytah/data/mazurka30-1.mid')
   
    # Runs repytah code and builds the list with no overlaps that contains start beat and end beat information
    lst = setup()
    #subtract 1 from the first beat because 1 indexed
    #Amanda helped me with the bounds here, I don't remember why we don't subtract 1 from both
    play_segment(lst[7][0]-1,lst[7][1], mid, outport)
    time.sleep(5)
    play_segment(lst[7][2]-1,lst[7][3], mid, outport)

    #work with this
    # play_segment(lst[0][0]+11, lst[0][1]+12, mid, outport)
    # time.sleep(3)
    # play_segment(lst[0][2]+11, lst[0][3]+12, mid, outport)

#plays a segment of a file given a start beat and an end beat
def play_segment(start_beat, end_beat, midi_file, outport):
    #used to keep a marker of what second number we are at in the song. necessary because each message is a different length
    time_counter = 0
    #convert given beats into seconds for segmentation while playing
    start_sec = beats2second(start_beat, midi_file.ticks_per_beat, get_tempo(midi_file))  
    end_sec = beats2second(end_beat, midi_file.ticks_per_beat, get_tempo(midi_file))

    #this code chunk is from mido docs, but altered to just play a part of the file 
    for msg in midi_file:
        #start a file at a certain point
        #when a midi_file is played the time attribute refers to time in seconds
        if (time_counter < start_sec):
            time.sleep(0)
        #end a file at a certain point
        elif (time_counter > end_sec):
            outport.panic()
            break
        else:
            time.sleep(msg.time)
            if not msg.is_meta:
                outport.send(msg)
        time_counter += msg.time

setup()
midi_player()