#!/usr/bin/env python3

import json
import queue
import sys
import logging
from slack import WebClient, RTMClient
from os import environ
from time import sleep
from threading import Thread
from requests import get
from datetime import datetime, timedelta

class SlackBot:

    def __init__( self ):
        logging.info( "[ + ] Creating SlackBot instance..." )
        self.channel = "#schedule"
        try:
            token = environ["SLACK_BOT_TOKEN"]
            self.client = WebClient( token = token )
        except:
            logging.error( "[ - ] Error starting slack.WebClient instance" )
            
        
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
    @RTMClient.run_on( event = "message" )
    def say_hello( **payload ):
        data = payload[ "data" ]
        if "hello" in data[ "text" ]:
            self.send_message( self, "RTM: Hello" )
    '''

            
    '''
    def rtm_worker( self ):
        logging.info( "[ + ] Starting Slack RTM worker" )
        try:
            self.client.rtm_connect()
            while True:
                try:
                    events = self.client.rtm_read()
                except:
                    loggin.error( "[ - ] Could not read RTM events" )
                    
                    if len( events ):
                        logging.info( "[ + ] New RTM event!" )

                        for e in events:
                            logging.debug( "[ + ] Event: {}".format( e ) )
                        
                sleep( 1 )
        except e:
            logging.error( "[ - ] Failed starting RTM session: {}".format( e ) )
    '''
    
    '''
    def run( self ):
        self.join_channel( self.channel )
        t = Thread( target = self.rtm_worker )
        t.start()
        sleep( 1 )
        return t
    '''
    
            
class BandeirasTime:

    def __init__( self ):
        logging.info( "[ + ] Creating BandeirasTime instance..." )
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

    
    def alert( self, eid ):        
        self.slack_bot.send_message( "Event \"{}\" starting. (Weight: {})\nGood Luck! 🚩".format(
            self._events[ eid ][ "title" ],
            self._events[ eid ][ "weight" ]
        ) )

        
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

    
    def reminder_worker( self ):
        logging.info( "[ + ] Starting Reminder worker" )

        q = self.queue        
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

        
    def reminder( self ):
        t = Thread( target = self.reminder_worker )
        t.start()
        sleep( 1 )
        return t
    
   
           

def main():
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
        handlers = [ logging.StreamHandler() ]
    )
    
    bandeiras = BandeirasTime()
    bandeiras.slack_bot.run()
    t = bandeiras.reminder()

    # do something meanwhile

    t.join()

if __name__ == "__main__":
    main()
