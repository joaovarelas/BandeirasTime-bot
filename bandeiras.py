#!/usr/bin/env python3

import json
import queue
import sys
import logging
from os import environ
from time import sleep
from requests import get
from datetime import datetime, timedelta



class BandeirasTime:

    def __init__( self, slack_client, main_channel ):
        logging.info( "[ + ] Creating BandeirasTime instance..." )
        
        self.slack_client = slack_client
        self.main_channel = main_channel

        self.queue = queue.Queue()
        self.events = list()
        self._events = dict() # stored twice

        
    def request( self, params ):
        url = "https://ctftime.org/api/v1/events/"
        headers = { "User-Agent" : "BandeirasTime v1" }
        
        logging.info( "[ + ] Getting events from CTF Time API..." )
        try:
            r = get( url, params = params, headers = headers )
        except:
            logging.error( "[ - ] Error getting events from CTF Time API" )

        data = json.loads( r.text )
        return data

    def get_events( self, days_prev = 0, days_next = 10, limit = 5 ):
        params = { "start" : self.unixtime( days_prev ),
                   "finish" : self.unixtime( days_next ),
                   "limit" : limit }
        
        return self.request( params )
    
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

        
    def events_str( self ):
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
                
        return msg

    
    def alert( self, eid ):
        msg = "Event \"{}\" starting. (Weight: {})\nGood Luck! 🚩".format(
            self._events[ eid ][ "title" ],
            self._events[ eid ][ "weight" ]
        ) 
        self.slack_client.chat_postMessage( channel = self.main_channel, text = msg )

        

    def init_queue( self ):
        logging.info( "[ + ] Resetting queue & events" )
        self.queue.queue.clear()
        self._events.clear()
        self.events = self.get_events()
        overlap = dict()

        delta = 1 * 60 * 60 # 1 hour
        
        for e in self.events:
            eid = int( e[ "id" ] )
            time = self.date_time( e[ "start" ] ) - delta # alert 1h before
            self._events[ eid ] = e

            while time in overlap.keys():
                time += 60
                overlap[ time ] = True

            logging.info( "[ + ] Adding event \"{}\" to queue.".format( e[ "title" ] ) )
            self.queue.put( ( eid, time ) )
            
            msg = "Added event \"{}\" to queue. (Starting in {:0>8})".format(
                e[ "title" ],
                str( self.seconds_timestamp( time - self.now() + delta ) )
            )
            #self.slack_client.chat_postMessage( channel = self.main_channel, text = msg )
            
    
    def reminder_worker( self ):
        logging.info( "[ + ] Starting Reminder worker" )

        self.init_queue()
        q = self.queue
        
        while not q.empty():
            e = q.get()
            eid = e[0]
            start = e[1]
            now = int( datetime.now().timestamp() )
            sleep_time = start - now
            
            
            msg = "Event \"{}\" starts in {:0>8}. Reminder in {} seconds.".format(
                self._events[ eid ][ "title" ],
                str( timedelta( seconds = sleep_time ) ),
                sleep_time )
            
            #self.slack_client.chat_postMessage( channel = self.main_channel, text = msg )
            
            sleep( sleep_time ) # handle interrupts
            
            self.alert( eid )

        logging.info( "[ + ] Queue empty. Restarting worker..." )
        
        #self.init_queue()
        self.reminder_worker()
        
   
           
'''
def main():
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
        handlers = [ logging.StreamHandler() ]
    )
    
    bandeiras = BandeirasTime()
    #bandeiras.slack_bot.run()
    t = bandeiras.reminder()

    # do something meanwhile

    t.join()

if __name__ == "__main__":
    main()
'''
