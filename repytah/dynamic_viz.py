import mido 
import time
import numpy as np

from .example import load_ex_data, csv_to_aligned_hierarchies
from .utilities import create_sdm, find_initial_repeats
from .search import find_complete_list
from .transform import remove_overlaps

"""
dynamic_viz.py

The beginnings of the Dynamic Visualization Project. This module contains 
functions to set up a MIDI port and then play segments of MIDI files. Also
generates a list of repeats 

The module contains the following functions:
    
    * setup
        Builds a list of repeats for a musical track

    * second2beat
        Currently unused helper method, converts seconds into beats.

    * beat2second
        Converts beats into seconds.

    * get_tempo
        Calculates the tempo of a file

    * midi_player
        Sets up a port and reads in the midi file, then plays 2 matching 
        segments of the file

    * play_segment
        Plays a segment of a file given a start beat and an end beat.

"""


def setup():
    """
    Builds a list of repeats within a song file, code mostly borrowed 
    from the repytah quicksetup docs.

    Returns:
        An list of pairs of repeats with no overlaps and annotations marked. This 
        is represented by an array of arrays. Each row is a different pair of repeats.
        Column 0: start beat of first instance
        Column 1: end beat of first instance
        Column 2: start beat of second instance
        Column 3: start beat of third instance
        Column 4: length of the repetition in beats
        Column 5: annotation marker
                                   
    """

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
    
    lst_no_overlaps = remove_overlaps(complete_lst, song_length)[0]
    return lst_no_overlaps
 

def second2beat(time, ticks_per_beat, tempo):
    """
    Calculates beats given seconds. Currently unused 

    Args:
        time (int): 
            In seconds, number that will be used to calculate beats
        
        ticks_per_beat (int):
            Represents the resolution of the file, remains fixed throughout
            a track. Accessible as file.ticks_per_beat

        tempo (int):
            Tempo of the MIDI track, in microseconds per quarter note. Accessible
            with the get_tempo() helper method
            

    Returns:
        The number of beats translated from a given number of seconds

    """

    ticks = mido.second2tick(time,ticks_per_beat, tempo)
    beat_num = ticks/ticks_per_beat
    return beat_num


def beats2second(beat, ticks_per_beat, tempo):
    """
    Calculates seconds given beats.

    Args:
        beat (int): 
            Given number of beats
        
        ticks_per_beat (int):
            Represents the resolution of the file, remains fixed throughout
            a track. Accessible as file.ticks_per_beat

        tempo (int):
            Tempo of the MIDI track, in microseconds per quarter note. Accessible
            with the get_tempo() helper method
            

    Returns:
        The number of seconds translated from a given number of beats

    """

    tick = beat*ticks_per_beat
    return mido.tick2second(tick, ticks_per_beat, tempo)


def get_tempo(midi_file):
    """
    Looks throughout the file for a set tempo message, then returns that as the 
    tempo. Code taken from a mido discussion on GitHub

    Args:
        midi_file (MidiFile): 
            Any MidiFile (the object mido creates for MIDI files)
                    
    Returns:
        The track's tempo, an integer

    """

    for track in midi_file.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    return msg.tempo

def midi_player():
    """
    Current driver method for MIDI related code. Sets up a port through GarageBand to play MIDI files, 
    then reads in and initializes a MIDI file. Builds the corresponding list of repeats, 
    then accesses it to play a set of repeating segments.

    """
    
    #sets up port through garageband, currently IAC Driver Bus 1 is the default port on mac
    #to set up on a mac, follow the steps in the answer here: https://stackoverflow.com/questions/40498625/outputting-midi-sound-from-python-mido-library-on-mac
    outport = mido.open_output('IAC Driver Bus 1')
    #reads in midi file
    mid = mido.MidiFile('repytah/data/mazurka30-1.mid')
   
    #builds the list with no overlaps
    lst = setup()

    # subtract 1 from the first beat because 1 indexed
    # don't subtract from second beat because non inclusive
    play_segment(lst[7][0]-1,lst[7][1], mid, outport)
    time.sleep(5)
    play_segment(lst[7][2]-1,lst[7][3], mid, outport)

def play_segment(start_beat, end_beat, midi_file, outport):
    """
    Plays a segment of a MIDI file given a start beat and end beat through a port.
    Converts beats to seconds (since aligned hierarchies are in beats and the mido player
    is in seconds). Then iterates through all the messages within the MIDI file, aggregating 
    the length of each message. When time is between the start beat and end beat the messages 
    are sent to the port and the file plays.

    Args:
        start_beat (int): 
            First beat that will be played  
        
        end_beat(int):
            Last beat that will be played

        midi_file (MidiFile):
            Midi file that the played segment will come from

        outport (Output):
            The port where the segment will play

    """
    #convert given beats into seconds for segmentation while playing
    start_sec = beats2second(start_beat, midi_file.ticks_per_beat, get_tempo(midi_file))  
    end_sec = beats2second(end_beat, midi_file.ticks_per_beat, get_tempo(midi_file))

    #used to keep a marker of what second we are at in the song. 
    # necessary because each message is a different length
    time_counter = 0

    for msg in midi_file:
        #start a file at a certain point
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


if __name__ == "__main__":
    midi_player()