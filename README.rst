A simple django app that responds to heartbeat polls.  

In a cluster of load-balanced web servers, this allows you to take a server out of service gracefully,
by letting your load balancer know that the server is going down before shutting down.

To implement, add 'heartbeat' to INSTALLED_APPS in your Django settings file.

Use the following setting in your Django settings file to specify what to check:
::

    HEARTBEAT = {
        'flag': {
            'class': 'heartbeat.heartbeats.Flag',
            'actions': {'takedown': True, 'mail_admins': True},
            'filename': '/etc/heart.beat'
        },
        'database': {
            'class': 'heartbeat.heartbeats.Db',
            'actions': {'takedown': True, 'mail_admins': True},
        },
        'cache': {
            'class': 'heartbeat.heartbeats.Cache',
            'actions': {'takedown': True, 'mail_admins': True},
        },
        'solr': {
            'class': 'curio.heartbeats.Solr',
            'actions': {'takedown': True, 'mail_admins': True},
            'url': SOLR_URL,
            'search_term': '*:*'
        },
    }

HEARTBEAT['flag'] is mandatory for the heartbeat command to work. This is the initial project goal.

The others are up to you. HEARBEAT['database'] and HEARTBEAT['cache'] are also included in the heartbeat module by default.


The 3 default checks (flag, db and cache) supports 2 actions:
 takedown: specify whether or not to return the 503 status in case of your check returns False.
 mail_admins: specify whether or not to mail the site admins if your check returns False.


Check the HEARBEAT['solr'] example to include project relative checks.
::


    ------------------ myapp.heartbeats.py -----------------------

    import pysolr
    from heartbeat.heartbeats import Check


    class Solr(Check):
        """
        Check if search_term returns results.
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


