# deals with messages that are generated by:
# https://github.com/jkelabora/snsnotify-plugin

import re
from lib.base_message_interface import BaseMessageInterface
from sounds.player import Player
import collections

base_animation_colours = [[0,0,250],[0,0,225],[0,0,200],[0,0,175],[0,0,150],[0,0,125],[0,0,100],[0,0,75],[0,0,50],[0,0,25],
    [0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],
    [0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]


first_led_range = collections.deque(xrange(len(base_animation_colours[0:20])))
second_led_range = collections.deque(xrange(len(base_animation_colours[0:12])))


# the keys in STAGES need to be case-sensitive matches of the jenkins build names
first_pipeline = {
    'OFFSET' : 0,
    'STAGE_WIDTH' : 4,
    'STAGES' : {
        'Prepare' : 0,
        'Unit Tests' : 1,
        'Integration Tests' : 2,
        'Deploy Test' : 3,
        'Deploy to QA' : 4,
        'Deploy to Production' : 5
        }
}

# the keys in STAGES need to be case-sensitive matches of the jenkins build names
second_pipeline = {
    'OFFSET' : 20,
    'STAGE_WIDTH' : 4,
    'STAGES' : {
        'DT - Prepare' : 0,
        'DT - Unit Test' : 1,
        'DT - Deploy Test' : 2,
        'DT - Deploy QA' : 3
        }
}


class Pipeline:
    def __init__(self, detail, led_range):
        self.base_message_interface = BaseMessageInterface()
        self.detail = detail
        self.led_range = led_range

    def issue_all_off(self):
        self.base_message_interface.issue_all_off()

    def issue_start_build(self):
        pipeline_length = self.detail['STAGE_WIDTH'] * (len(self.detail['STAGES'])-1) # exclude the Prepare stage

        for pixel in xrange(self.detail['OFFSET'], pipeline_length):
            self.led_range.rotate(1)
            self.base_message_interface.issue_start_build_step(pixel, base_animation_colours[self.led_range[0]][0],
                base_animation_colours[self.led_range[0]][1], base_animation_colours[self.led_range[0]][2])
        self.led_range.rotate((len(self.led_range)-1))

    def issue_all_stages_update(self, colour):
        tokens = [self.detail['OFFSET'], (len(self.detail['STAGES'])-1), self.detail['STAGE_WIDTH'], colour] # exclude the Prepare stage
        extras = ['blue'] * (len(self.detail['STAGES'])-2) # exclude the Prepare and first stages
        self.base_message_interface.issue_update(tokens + extras)

    def issue_update_segment(self, segment_number, colour):
        tokens = [self.detail['OFFSET'], self.detail['STAGE_WIDTH'], segment_number, colour]
        self.base_message_interface.issue_update_segment(tokens)

    def determine_segment_number(self, message):
        match = re.search(jenkins_regex, message)
        return self.detail['STAGES'][match.group(2)]


# the keys here are from the snsnotify-plugin, the values need to match the base_message_interface colours
jenkins_colours = {
    'FAILURE' : 'red',
    'SUCCESS' : 'green',
    'ABORTED' : 'white'
}

def determine_colour(message):
    match = re.search(jenkins_regex, message)
    return jenkins_colours[match.group(1)]


# pick out the required parts from the snsnotify-plugin messages
jenkins_regex = r"Build ([A-Z]+): (.*) #"


class JenkinsMessageTranslator:

    def __init__(self):
        self.pipelines = [Pipeline(first_pipeline, first_led_range), Pipeline(second_pipeline, second_led_range)]
        self.sound_player = Player()

    def determine_pipeline(self, directive):
        build_name = re.search(jenkins_regex, directive).group(2)
        if re.match('^DT', build_name):
            return self.pipelines[1]
        else:
            return self.pipelines[0]

    def issue_directive(self, directive, play_sound=False):

        if directive == 'all_off':
            self.pipelines[0].issue_all_off() # any pipeline will do
            return

        pipeline = self.determine_pipeline(directive)
        segment_number = pipeline.determine_segment_number(directive)

        if segment_number == 0:
            pipeline.issue_start_build()
            if play_sound:
              self.sound_player.play_random_start_sound()
            return

        colour = determine_colour(directive)
        if play_sound:
          if colour == 'green':
            self.sound_player.play_random_success_sound()
          elif colour == 'red':
            self.sound_player.play_random_failure_sound()

        if segment_number == 1:
            pipeline.issue_all_stages_update(colour)
            return

        pipeline.issue_update_segment(segment_number, colour)
