#!/usr/bin/env python3

import logging
from os import environ
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from threading import Thread

from bandeiras import BandeirasTime


client = WebClient( token = environ[ "SLACK_BOT_TOKEN" ] )
events = SlackEventAdapter( environ[ "SLACK_SIGNING_SECRET" ], "/slack/events" )

main_channel = "#schedule"
bandeiras = BandeirasTime( client, main_channel )

cmd_prefix = "!ctf"


def handle_command( cmd ):
    lst = cmd.split(" ")
    if lst[1] == "events":
        msg = bandeiras.events_str()
        client.chat_postMessage( channel = main_channel, text = msg )
        


@events.on( "message" )
def message( payload ):
    event = payload.get( "event", {} )
    channel_id = event.get( "channel" )
    user_id = event.get( "user" )
    text = event.get( "text" )
    
    if text and text[ : len( cmd_prefix ) ] == cmd_prefix:
        handle_command( text )
        # client.chat_postMessage( channel = channel_id, text = "PONG" )
        
    

def main():
    
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
        handlers = [ logging.StreamHandler() ]
    )
    
    
    t1 = Thread( target = bandeiras.reminder_worker )
    t2 = Thread( target = events.start, args = ( '127.0.0.1' , 3000 , False, ) )

    t1.start()
    t2.start()
    
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()


    








    

'''
class SlackBot:

    def __init__( self ):
        logging.info( "[ + ] Creating SlackBot instance..." )
        self.channel = "#schedule"
        try:
            token = environ[ "SLACK_BOT_TOKEN" ]
            self.client = WebClient( token = token )
        except:
            logging.error( "[ - ] Error starting SlackBot instance" )
            
        
    def join_channel( self, channel ):
        logging.info( "[ + ] Joining channel" )
        try:
            self.client.channels_join( name = channel )
        except:
            logging.error( "[ - ] Error joining channel: {}".format( channel ) )
            
    def send_message( self, msg ):
        logging.info( "[ + ] Sending message" )
        try:
            self.client.chat_postMessage( channel = self.channel, text = msg )
        except:
            logging.error( "[ - ] Error sending message: {}".format( msg ) )

                  
    def run( self ):
        self.join_channel( self.channel )
'''

        
