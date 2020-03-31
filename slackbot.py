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
              #"subscribe - Receive notifications of events",
              "events - Get detailed list of events",
              "schedule - Current events on schedule",
              "addevent id_1 id_2 ... id_n - Add event(s) to schedule",
              "delevent id_1 id_2 ... id_n - Remove event(s) from schedule" ]



def handle_command( payload ):

    #    try:
    event = payload.get( "event", {} )
    cmd = event.get( "text" ).split(" ")
    action = cmd[1]

    logging.info( "[ + ] Received action {}".format( action ) )
    
    if action == "help":
        msg = ""
        for h in help_menu:
            msg += "{} {}\n".format( cmd_prefix, h )
        client.chat_postMessage( channel = event.get( "channel" ), text = msg )

    elif action == "subscribe":
        msg = "Successfully subscribed to CTF events reminder!"
        client.chat_postMessage( channel = event.get( "channel" ), text = msg ) 
        
    elif action == "events":
        msg = bandeiras.print_events()
        client.chat_postMessage( channel = event.get( "channel" ), text = msg )

    elif action == "schedule":
        if not bandeiras.schedule:
            msg = "Schedule is empty."
            client.chat_postMessage( channel = event.get( "channel" ), text = msg )
            return
        
        msg = "There are {} events scheduled:".format( len( bandeiras.schedule ) )
        client.chat_postMessage( channel = event.get( "channel" ), text = msg )
        
    elif action == "addevent":
        if len( cmd ) > 2:
            ids = cmd[2:]
            for i in ids:
                bandeiras.add_event( i )

            msg = "Added {} event(s).".format( len( cmd[2:] ) )
            client.chat_postMessage( channel = event.get( "channel" ), text = msg )
            
    elif action == "delevent":
        if len( cmd ) > 2:
            ids = cmd[2:]
            for i in ids:
                bandeiras.del_event( i )

            msg = "Deleted {} event(s).".format( len( cmd[2:] ) )
            client.chat_postMessage( channel = event.get( "channel" ), text = msg )
            
    else:
        _ = 1
        
   # except:
   # logging.error( "[ - ] Error handling command: {}".format( cmd ) )
        

unique_events = set()
@events.on( "message" )
def message( payload ):
    logging.info( "[ + ] New SlackAPI event received: " ) #{}".format( payload ) )
    event = payload.get( "event", {} )
    
    # ignore repeated POST events from slackapi (?)
    unique_id = payload.get( "event_id" )
    if unique_id in unique_events:
        return
    unique_events.add( unique_id )

    # ignore own bot messages
    bot_id = event.get( "bot_id" )
    if bot_id and bot_id == "B010JEJE807":
        return

    # parse command
    text = event.get( "text" )
    if text and text[ : len( cmd_prefix ) ] == cmd_prefix:
        handle_command( payload )
        

def main(): 
    logging.basicConfig(
        format = "%(asctime)s [%(levelname)s] %(message)s",
        handlers = [ logging.StreamHandler() ],
        level = logging.INFO
    )
    
    
    t1 = Thread( target = bandeiras.reminder_worker )
    t2 = Thread( target = events.start, args = ( '0.0.0.0' , 3000 , False, ) )

    t1.start()
    t2.start()
    
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()


