import json
import queue
import sys
from time import sleep
from threading import Thread
from requests import get
from datetime import datetime, timedelta


class BandeirasTime:

    def __init__( self ):
        self.queue = queue.Queue()
        self.events = list()
        self._events = dict() # stored twice
        
    def init_queue( self ):
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
            self.queue.put( ( eid, time ) )

                                
    def get_events( self, days_prev = 0, days_next = 10, limit = 20 ):
        params = { "start" : self.timestamp( days_prev ),
                   "finish" : self.timestamp( days_next ),
                   "limit" : limit }

        return self.request( params )

    def reminder( self ):
        t = Thread( target = self.reminder_thread )
        t.start()
        return t

    def reminder_thread( self ):
        q = self.queue
        
        while not q.empty():
            e = q.get()
            start = e[1]
            now = int( datetime.now().timestamp() )
            sleep_time = start - now
            
            print( "Event \"{}\" starts in {:0>8}. Sleeping for {} seconds..."
                   .format( self._events[ e[0] ][ "title" ],
                            str( timedelta( seconds = sleep_time ) ),
                            sleep_time ) )

            sleep( sleep_time ) # handle interrupt
            
            self.alert( e[0] )

        self.init_queue()
        self.reminder_thread()

        
    def alert( self, eid ):        
        print( "Event \"%s\" starting..." % ( self._events[ eid ][ "title" ] ) )
        
    def request( self, params ):
        url = "https://ctftime.org/api/v1/events/"
        headers = { "User-Agent" : "BandeirasTime v1" }

        r = get( url, params = params, headers = headers )        
        return json.loads( r.text )

    def timestamp( self, days = 0 ):
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

        
    def print( self ):
        keys = [ "title", "start", "finish", "weight", "location",
                 "url", "ctf_id", "ctftime_url",  "id"]

        for d in self.events:
            print("")
            for k in keys:
                if d[ k ]:
                    print( "%s: %s" % ( k, d[ k ] ) )
                    


def main():
    bandeiras = BandeirasTime()
    bandeiras.init_queue()
    t = bandeiras.reminder()

    # do something meanwhile
    
    t.join()

if __name__ == "__main__":
    main()
