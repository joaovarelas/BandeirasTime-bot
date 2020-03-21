#!/usr/bin/env python3

import json
import queue
import sys
import slack
import logging
from os import environ
from time import sleep
from threading import Thread
from requests import get
from datetime import datetime, timedelta


class SlackBot:

    def __init__( self ):
        try:
            self.slack_client = slack.WebClient( token = environ["SLACK_BOT_TOKEN"] )
        except:
            logging.error( "[ - ] Error starting slack.WebClient instance" )
            
        self.channel = "#schedule"
        
    def join_channel( self, channel ):
        try:
            logging.info( "[ + ] Joining channel" )
            self.slack_client.channels_join( name = channel )
        except:
            logging.error( "[ - ] Error joining channel: {}".format( channel ) )
            
    def send_message( self, msg ):
        try:
            logging.info( "[ + ] Sending message" )
            self.slack_client.chat_postMessage( channel = self.channel, text = msg )
        except:
            logging.error( "[ - ] Error sending message: {}".format( msg ) )
            
    def parse_command( self, cmd ):
        try:
            logging.info( "[ + ] Parsing command" )
            # parse
        except:
            logging.error( "[ - ] Error parsing command: {}".format( cmd ) )
            
class BandeirasTime:

    def __init__( self ):
        logging.info( "[ + ] Starting SlackBot instance..." )
        self.slack_bot = SlackBot()
        self.queue = queue.Queue()
        self.events = list()
        self._events = dict() # stored twice

    def init_queue( self ):
        logging.info( "[ + ] Resetting queue & events" )
        self.queue.queue.clear()
        self._events.clear()
        self.events = self.get_events()
        overlap = dict()

        for e in self.events:
            eid = int( e[ "id" ] )
            time = self.date_time( e[ "start" ] )
            self._events[ eid ] = e

            while time in overlap.keys():
                time += 60

            overlap[ time ] = True

            logging.info( "[ + ] Adding event \"{}\" to queue.".format( e[ "title" ] ) )
            self.queue.put( ( eid, time ) )
            
            
            self.slack_bot.send_message( "Added event \"{}\" to queue. (Starting in {:0>8})".format(
                e[ "title" ],
                str( self.seconds_timestamp( time - self.now()  ) )
            ) )

                                
    def get_events( self, days_prev = 0, days_next = 10, limit = 5 ):
        params = { "start" : self.unixtime( days_prev ),
                   "finish" : self.unixtime( days_next ),
                   "limit" : limit }
        return self.request( params )

    
    def reminder( self ):
        logging.info( "[ + ] Starting reminder worker thread..." )
        t = Thread( target = self.reminder_worker )
        t.start()
        return t

    
    def reminder_worker( self ):
        q = self.queue

        self.slack_bot.join_channel( "#schedule" )
        
        while not q.empty():
            e = q.get()
            eid = e[0]
            start = e[1]
            now = int( datetime.now().timestamp() )
            sleep_time = start - now
            
            '''
            msg = "Event \"{}\" starts in {:0>8}. Reminder in {} seconds.".format(
                self._events[ eid ][ "title" ],
                str( timedelta( seconds = sleep_time ) ),
                sleep_time )
            self.slack_bot.send_message( msg )
            '''
            
            sleep( sleep_time ) # handle interrupts
            self.alert( eid )

        logging.info( "[ + ] Queue empty. Restarting worker..." )
        self.init_queue()
        self.reminder_worker()

        
    def alert( self, eid ):        
        self.slack_bot.send_message( "Event \"{}\" starting. (Weight: {})\nGood Luck! 🚩".format(
            self._events[ eid ][ "title" ],
            self._events[ eid ][ "weight" ]
        ) )

        
    def request( self, params ):
        url = "https://ctftime.org/api/v1/events/"
        headers = { "User-Agent" : "BandeirasTime v1" }
        
        try:
            logging.info( "[ + ] Getting events from CTF Time API..." )
            r = get( url, params = params, headers = headers )
        except:
            logging.error( "[ - ] Error getting events from CTF Time API" )

        data = json.loads( r.text )
        return data

    def unixtime( self, days = 0 ):
        delta = timedelta( days = days )
        time = datetime.now()
        time += delta if days >= 0 else -delta
        return int( ( datetime.now() + timedelta( days = days ) ).timestamp() )

    def date_time( self, _date ):
        date = _date.split( "T" )[ 0 ].split( "-" )
        year, month, day = [ int( x ) for x in date ]
        time = _date.split( "T" )[ 1 ].split( "+" )[ 0 ].split( ":" )
        hour, minute, sec =  [ int( x ) for x in time ]
        return int( datetime( year, month, day, hour, minute, sec ).timestamp() )

    def seconds_timestamp( self, secs ):
        return timedelta( seconds = secs )

    def now( self ):
        return self.unixtime()

        
    def _print( self ):
        keys = [ "title", "start", "finish", "weight", "location",
                 "url", "ctf_id", "ctftime_url",  "id"]
        msg = ""
        for e in self.events:
            msg += "\n"
            print("")
            for k in keys:
                line = "%s: %s\n" % ( k, e[ k ] )
                msg += line
                print( line )
                
        self.slack_bot.send_message( msg )
        

        

def main():
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
        handlers = [ logging.StreamHandler() ]
    )
    
    logging.info( "[ + ] Starting BandeirasTime..." )
    
    bandeiras = BandeirasTime()
    bandeiras.init_queue()
    t = bandeiras.reminder()

    # do something meanwhile
    
    t.join()

if __name__ == "__main__":
    main()
