"""
Class to help with creation of initd scripts.

Use this in conjunction with the DaemonCommand management command base class.
"""
from __future__ import print_function


import logging, os, signal, sys, time, errno

__all__ = ['start', 'stop', 'restart', 'status', 'execute']

class Initd(object):
    def __init__(self, log_file='', pid_file='', workdir='', umask='', 
                 stdout='', stderr='', **kwargs):
        self.log_file = log_file
        self.pid_file = pid_file
        self.workdir = workdir
        self.umask = umask
        self.stdout = stdout
        self.stderr = stderr

    def start(self, run, exit=None):
        """
        Starts the daemon.  This daemonizes the process, so the calling process
        will just exit normally.

        Arguments:
        * run:function - The command to run (repeatedly) within the daemon.

        """
        # if there's already a pid file, check if process is running
        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as stream:
                pid = int(stream.read())
            try:
                # sending 0 signal doesn't do anything to live process, but 
                # will raise error if process doesn't exist
                os.kill(pid, 0)
            except OSError:
                pass
            else:
                logging.warn('Daemon already running.')
                return

        from django.utils.daemonize import become_daemon
        become_daemon(self.workdir, self.stdout, self.stderr, self.umask)

        _initialize_logging(self.log_file)
        _create_pid_file(self.pid_file)

        # workaround for closure issue is putting running flag in array
        running = [True]
        def cb_term_handler(sig, frame):
            """
            Invoked when the daemon is stopping.  Tries to stop gracefully
            before forcing termination.
            
            The arguments of this function are ignored, they only exist to
            provide compatibility for a signal handler.

            """
            if exit:
                logging.debug('Calling exit handler')
                exit()
            running[0] = False
            def cb_alrm_handler(sig, frame):
                """
                Invoked when the daemon could not stop gracefully.  Forces
                exit.

                The arguments of this function are ignored, they only exist to
                provide compatibility for a signal handler.

                """
                logging.warn('Could not exit gracefully.  Forcefully exiting.')
                sys.exit(1)
            signal.signal(signal.SIGALRM, cb_alrm_handler)
            signal.alarm(5)

        signal.signal(signal.SIGTERM, cb_term_handler)

        logging.info('Starting')
        try:
            while running[0]:
                try:
                    run()
                # disabling warning for catching Exception, since it is the
                # top level loop
                except Exception as exc: # pylint: disable-msg=W0703
                    logging.exception(exc)
        finally:
            os.remove(self.pid_file)
            logging.info('Exiting.')


    def stop(self, run=None, exit=None):
        """
        Stops the daemon.  This reads from the pid file, and sends the SIGTERM
        signal to the process with that as its pid.  This will also wait until
        the running process stops running.
        """
        try:
            with open(self.pid_file, 'r') as stream:
                pid = int(stream.read())
        except IOError as ioe:
            if ioe.errno != errno.ENOENT:
                raise
            sys.stdout.write('Stopped.\n')
            return
        sys.stdout.write('Stopping.')
        sys.stdout.flush()
        os.kill(pid, signal.SIGTERM)
        while os.path.exists(self.pid_file):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.5)
        sys.stdout.write('\n')


    def restart(self, run, exit=None):
        """
        Restarts the daemon.  This simply calls stop (if the process is running)
        and then start again.

        Arguments:
        * run:function - The command to run (repeatedly) within the daemon.
        """
        if os.path.exists(self.pid_file):
            self.stop(self.pid_file)
        print('Starting.')
        self.start(run, exit=exit)


    def status(self, run=None, exit=None):
        """
        Prints the daemon's status:
        'Running.' if is started, 'Stopped.' if it is stopped.
        """
        if os.path.exists(self.pid_file):
            sys.stdout.write('Running.\n')
        else:
            sys.stdout.write('Stopped.\n')
        sys.stdout.flush()


    def execute(self, action, run=None, exit=None):
        cmd = getattr(self, action)
        cmd(run, exit)


def _initialize_logging(log_file):
    """
    Initializes logging if a log_file parameter is specified in config
    config.  Otherwise does not set up any log.
    
    Arguments:
    * log_file:str - The path to the log file, or None if no logging
                     should take place.

    """
    if log_file:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s',
                            filename=log_file,
                            filemode='w')


def _create_pid_file(pid_file):
    """
    Outputs the current pid to the pid file specified in config.  If the
    pid file cannot be written to, the daemon aborts.

    Arguments:
    * pid_file:str - The path to the pid file.

    """
    try:
        with open(pid_file, 'w') as stream:
            stream.write(str(os.getpid()))
    except OSError as err:
        logging.exception(err)
        logging.error('Failed to write to pid file, exiting now.')
        sys.exit(1)
