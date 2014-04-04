A simple django app that responds to heartbeat polls.  

In a cluster of load-balanced web servers, this allows you to take a server out of service gracefully,
by letting your load balancer know that the server is going down before shutting down.

To implement, add 'heartbeat' to INSTALLED_APPS in your Django settings file.

Use the following setting in your Django settings file to specify what to check:

Services to check by the loadbalancer
::

    HEARTBEAT = {
        'flag': {
            'class': 'heartbeat.heartbeats.Flag',  # class of your checker
            'actions': {'takedown': True},  # actions you can implement
            'filename': '/Users/baillaan/desktop/h.beat'  # other params you can implement
        },
        'database': {
            'class': 'heartbeat.heartbeats.Db',
            'actions': {'takedown': False},
        },
        'cache': {
            'class': 'heartbeat.heartbeats.Cache',
            'actions': {'takedown': False},
        },
        'solr': {
            'class': 'myapp.heartbeats.Solr',
            'actions': {'takedown': False, 'mail_admins': True},
            'url': SOLR_URL,
            'search_term': '*:*'
        },
    }

HEARTBEAT['flag'] is mandatory for the heartbeat command to work. This is the initial project

The others are up to you. HEARBEAT['database'] and HEARTBEAT['cache'] are also included in the module now.

Check the HEARBEAT['solr'] example to make your own!
::


    ------------------ myapp.heartbeats.py -----------------------

    import pysolr
    from heartbeat.heartbeats import Check


    class Solr(Check):
        """
        Check if *:* returns results.
        @returns False if no results
        """
        def __init__(self, **params):
            super(Solr, self).__init__(**params)
            self.url = params.get('url')
            self.search_term = params.get('search_term')

        def perform_check(self):
            try:
                solr = pysolr.Solr(self.url, timeout=2)
                results = solr.search(self.search_term)
                if results.hits:
                    self.msg = 'Ok'
                    return True
                else:
                    self.msg = 'Fail to fetch results'
                    return False if self.actions.get('takedown') else True


    ------------------ myapp.heartbeats.py -----------------------


You can use the Django management commands to set or remove a flag:
::

    $ bin/django heartbeat down
    $ bin/django heartbeat up


Used with HAProxy, your HAProxy config file might contain this:
::

    backend site
        balance roundrobin
        option httpchk HEAD /heartbeat/status/ HTTP/1.0
        option httpclose
        server web-appserver-A-1 10.0.2.2:80 check inter 5000
        server web-appserver-A-2 10.0.2.3:80 check inter 5000
        server web-appserver-A-3 10.0.2.4:80 check inter 5000
        server web-appserver-B-1 10.0.5.2:80 check inter 5000
        server web-appserver-B-2 10.0.5.3:80 check inter 5000
        server web-appserver-B-3 10.0.5.4:80 check inter 5000


