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

help_menu = [ "help - Show available commands",
              "subscribe - Receive notifications of events",
              "events - Get detailed list of events"
              "addevent id_1 id_2 ... id_n - Add event(s) to schedule" ]



# TODO
def handle_command( payload ):
    
    try:
        event = payload.get( "event", {} )
        cmd = event.get( "text" ).split(" ")
        action = cmd[1]
        
        if action == "help":
            msg = ""
            for h in help_menu:
                msg += cmd_prefix + " " + h
            client.chat_postMessage( channel = main_channel, text = msg )

        elif action == "subscribe":
            msg = "Successfully subscribed to CTF events reminder!"
            client.chat_postMessage( channel = event.get( "user" ), text = msg ) 
            
        elif action == "events":
            msg = bandeiras.events_str()
            client.chat_postMessage( channel = event.get( "channel" ), text = msg )

        elif action == "addevent":
            _ = 1
            
        else:
            _ = 1
            
    except:
        logging.error( "[ - ] Error handling command: {}".format( cmd ) )
        


@events.on( "message" )
def message( payload ):
    logging.info( "[ + ] New event received: {}".format( payload ) )
    
    text = payload.get( "event", {} ).get( "text" )
    if text and text[ : len( cmd_prefix ) ] == cmd_prefix:
        handle_command( payload )
        

def main():
    
    logging.basicConfig(
        format = "%(asctime)s [%(levelname)s] %(message)s",
        handlers = [ logging.StreamHandler() ],
        level = logging.DEBUG
    )
    
    
    t1 = Thread( target = bandeiras.reminder_worker )
    t2 = Thread( target = events.start, args = ( '0.0.0.0' , 3000 , False, ) )

    t1.start()
    t2.start()
    
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()


