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
        logging.basicConfig(
            format = "%(asctime)s [%(levelname)s] %(message)s",
            handlers = [ logging.StreamHandler() ],
            level = logging.INFO
        )
        
        logging.info( "[ + ] Creating BandeirasTime instance..." )
        
        self.slack_client = slack_client
        self.main_channel = main_channel
        
        self.subscribers = set()
        self.schedule = set()
        self.one_hour = dict() # temp fix
        self.events = dict()

        self.delta = 1 * 60 * 60 # 1 hour span
        self.update_freq = 30 # 30 secs update

        
        
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

        self.events.clear()
        
        params = { "start" : self.unix_time( days_prev ),
                   "finish" : self.unix_time( days_next ),
                   "limit" : limit }

        
        json_data = self.request( params )
        for line in json_data:
            self.events[ line[ "id" ] ] = line

        return

    # temporary fix
    def get_weight( self, url ):
        headers = { "User-Agent" : "BandeirasTime v1" }
        r = get( url, headers = headers )
        html = r.text
        rating = html.split("Rating weight: ")[1].split("&")[0]
        return rating
        
    
    def unix_time( self, days = 0 ):
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
        return self.unix_time()

        
    def print_events( self ):
        self.get_events()
        
        msg = ""
        for k in self.events.keys():
            e = self.events[ k ]
            line = "ID: {} | {} | Weight: {} | Starts in: {:0>8}  | URL: {}\n".format(
                e[ "id" ],
                e[ "title" ],
                self.get_weight( e[ "ctftime_url" ] ),
                str( timedelta( seconds = self.date_time( e[ "start" ] ) - self.now() ) ),
                #e[ "weight" ],
                e[ "url" ]
            )
            msg += line
        return msg

    def print_schedule( self ):
       
        msg = ""
        for e in self.schedule:
            msg += "Event {} starting in {:0>8}\n".format(
                self.events[ e[ 1 ] ][ "title" ],
                str( timedelta( seconds = e[ 0 ] - self.now() ) )
            )
        logging.info(" [ + ] DEBUG: schedule: {}\n".format( msg ) )
        return msg
    
    def add_event( self, eid ):
        logging.info( "[ + ] Adding event to schedule" )
        eid = int( eid )
        start = self.date_time( self.events[ eid ][ "start" ] )
        self.schedule.add( ( start, eid ) )
        self.one_hour[ eid ] = False
        return

    def del_event( self, eid ):
        logging.info( "[ + ] Deleting event from schedule" )
        eid = int( eid )
        start = self.date_time( self.events[ eid ][ "start" ] )
        self.schedule.remove( ( start, eid ) )
        self.one_hour.pop( eid )
        return

    def reminder_worker( self ):
        logging.info( "[ + ] Starting Reminder worker" )
        
        while True:

            #print(self.events)
            print(self.schedule)
            print(self.one_hour)
            
            if not self.schedule:
                logging.info( "[ + ] Empty schedule. Sleeping..." )
                sleep( self.update_freq )
                continue

            tmp_schedule = self.schedule.copy()
            
            #logging.info( "[ + ] Schedule is not empty" )
            for e in self.schedule:
                start = e[0]
                eid = e[1]

                # event started
                if self.now() >= start:
                    logging.info( "[ + ] Starting event {}!".format( eid ) )
                    self.alert( eid )
                    logging.info( "[ + ] Removing event {} from schedule".format( eid ) )
                    
                    tmp_schedule.remove( (start, eid) ) # ghetto fix data race
                    
                    self.one_hour.pop( eid )
                    continue

                # 1 hour remaining
                if start - self.now() <= self.delta:
                    if self.one_hour[ eid ]:
                        continue
                    
                    logging.info( "[ + ] 1 Hour remaining for event {}".format( eid ) )
                    msg = "Event \"{}\" (Weight: {}) starting in {:0>8}.".format(
                        self.events[ eid ][ "title" ],
                        #self.events[ eid ][ "weight" ],
                        self.get_weight( self.events[ e[ 1 ] ][ "ctftime_url" ] ),
                        str( timedelta( seconds = start - self.now() ) )
                    )
                    
                    self.one_hour[ eid ] = True
                    self.slack_client.chat_postMessage( channel = self.main_channel, text = msg )
                    continue

            self.schedule = tmp_schedule.copy()
            #logging.info( "[ + ] Checking schedule again. Sleeping..." )   
            sleep( self.update_freq )
        return
    

    def alert( self, eid ):
        msg = "Event \"{}\" starting. (Weight: {})\nGood Luck! 🚩".format(
            self.events[ eid ][ "title" ],
            self.get_weight( self.events[ eid ][ "ctftime_url" ] )
            #self.events[ eid ][ "weight" ]
        ) 
        self.slack_client.chat_postMessage( channel = self.main_channel, text = msg )
        return
    
