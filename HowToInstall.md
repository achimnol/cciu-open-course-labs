## Pre-requisites ##

  * Python 2.5 or higher
  * Django 1.1 or higher (MySQL/Postgres backend is recommended)
  * python-lxml, python-setuptools, python-paramiko (mandatory)
  * python-pygraphviz package (optional)
  * [django\_extensions](http://code.google.com/p/django-command-extensions/) (custom install)
  * A WSGI/FastCGI-compatible web server (mod\_wsgi 2.x or higher is recommended)
  * A SMTP server for user notifications

## Installation ##
(We focus on Apache 2.2 + mod\_wsgi on this document.)

  1. First, check out the code from the repository, or get the latest release and unpack it:
```
$ hg clone https://cciu-open-course-labs.googlecode.com/hg/ cciu-open-course-labs
```
  1. Create and configure `settings_local.py` by using `settings.py` as a reference, and at the same directory.<br>Most common attributes should be set are:<br>
<ul><li><code>ADMINS</code>
</li><li><code>DATABASE_*</code>
</li><li><code>REPOSITORY_STORAGE_PATH</code> (usually use <code>os.path.join(PROJECT_PATH, 'repository/storage')</code>)<br>
</li><li><code>EC2_*</code>
</li><li><code>ICUBE_*</code>
</li><li><b>Note:</b> If you choose MySQL as database engine, you should set the storage engine to InnoDB to enable transactions.<br /><code>DATABASE_OPTIONS = {'init_command': 'SET storage_engine=INNODB'}</code>
</li></ul><ol><li>After configuring <code>settings_local.py</code>, run the following command:<br>
<pre><code>$ ./manage.py syncdb<br>
</code></pre>
</li><li>You'll be asked to create an administrator account. Do it.<br>
</li><li>Next, you have to create the directory for repository (as set in <code>REPOSITORY_STORAGE_PATH</code>) and give the web server permission to write in it.<br>Running the test suite is a good habit, of course. :)</li></ol>

<h2>Running</h2>
You may just run a test-server delivered with Django:<br>
<pre><code>$ ./manage.py runserver 0.0.0.0:8080<br>
</code></pre>

Or, you may use Twisted-based server also:<br>
<code>TODO</code>

If you're going to use Apache Web Server, configure it like this and restart it:<br>
<pre><code>&lt;VirtualHost *&gt;<br>
    ServerName {PROJECT-HOSTNAME}<br>
    ServerAdmin root@localhost<br>
<br>
    DocumentRoot /{PROJECT-PATH}/htdocs<br>
<br>
    Alias /index.gif /{PROJECT-PATH}/media/index.gif<br>
    Alias /favicon.ico /{PROJECT-PATH}/media/favicon.ico<br>
    Alias /media/ /{PROJECT-PATH}/media/<br>
    Alias /media-admin/ /usr/lib/python2.5/site-packages/django/contrib/admin/media/<br>
<br>
    WSGIDaemonProcess {PROJECT-NICK} processes=3 threads=20 user=www-data group=www-data<br>
    WSGIProcessGroup {PROJECT-NICK}<br>
    WSGIScriptAlias / /{PROJECT-PATH}/django.wsgi<br>
<br>
    ErrorLog /var/log/apache2/cciu-error_log<br>
    CustomLog /var/log/apache2/cciu-access_log combined<br>
<br>
    &lt;Directory /{PROJECT-PATH}/htdocs&gt;<br>
        Order allow,deny<br>
        allow from all<br>
    &lt;/Directory&gt;<br>
    &lt;Directory /{PROJECT-PATH}/acciweb&gt;<br>
        Options ExecCGI SymLinksIfOwnerMatch<br>
        AllowOverride FileInfo<br>
        Order allow,deny<br>
        allow from all<br>
    &lt;/Directory&gt;<br>
<br>
&lt;/VirtualHost&gt;<br>
</code></pre>

You may have to change alias of <code>/media-admin/</code> according to your Python package directory.<br>
For details about WSGI config directives, <a href='http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives'>see its documentation.</a> (Note that <code>display-name</code> attribute of <code>WSGIDaemonProcess</code> directive is not supported by mod_wsgi 1.3)<br>
<br>
<h2>Customizing</h2>

CCI:U Open Course Labs uses Django's flatpages application. You can define your own static pages such as contact information, notices, help, terms of use, and etc. To do that, modify <code>fixtures/initial_data.xml</code> at the project directory and run <code>./manage.py syncdb</code>.<br>
<br>
Design is also modifieable via HTML templates and stylesheets as you need.<br>
<br>
<h2>Maintenance</h2>

There are some management commands for sustainable service operation. <code>clean_keypairs</code> and <code>clean_uploadtemp</code> requires themselves to be a scheduled job (usually cron), and recommended interval is from 30 minutes to a few hours depending on amount of service usage.<br>
<br>
<ul><li><code>./manage.py show_instances</code> : shows all instances registered by CCI:U Open Course Labs from all available backends.<br>
</li><li><code>./manage.py clean_instance</code> : If there is any running instance that should have been terminated, terminate it. That should not happen, but this command is provided for safety and debugging reason.<br>
</li><li><code>./manage.py clean_keypairs</code> : Similar to <code>clean_instance</code>, delete unnecessary keypairs. This is required because deleting keypairs used by existing instances may show different behaviours among cloud services. Some results failures on that situation, so we need delayed deletion as a scheduled job.<br>
</li><li><code>./manage.py clean_uploadtemp</code> : Clean up temporary files created by uploading process such as attaching a file to assignments. We cannot determine either that user has cancelled to upload or that there were network problems when the handling routine for uploaded files is not executed. This deletes temporary files which are at least 2-hours-old.