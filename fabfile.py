import time
from fabric.colors import green, yellow
from fabric.operations import local as lrun
from fabric.api import *
from fabric.contrib import *


""" These are settings specific to this site
"""
PRODUCTION_HOST='learning-docs.hauntdigital.co.nz'

web_docs_dir = '/var/www'
site_name = 'learning-docs'
release_dir = web_docs_dir + '/releases/' + site_name
sitedir = web_docs_dir + '/' + site_name
files_dir = web_docs_dir + '/files/' + site_name
service_name = site_name
project_name = site_name
webroot_mode = '775'
webroot_var_mode = '775'

if not env.hosts:
  env.hosts = [PRODUCTION_HOST]

env.forward_agent = True

def generate_pw(length=8):
  """ Returns a alphanumeric string of length
  """
  newpasswd = ''
  chars = string.letters + string.digits
  for i in range(length):
    newpasswd = newpasswd + chars[random.randint(0,len(chars)-1)]
  return newpasswd


def get_project_name(branch):
    """ Attempts to generate a project name given a branch """
    proj = local('pwd', capture=True).split('/')[-1]
    if branch == 'master':
        tstamp = time.strftime("%Y%m%d%H%M")
        project_name = proj+'-'+branch+'-'+tstamp
    else:
        project_name = proj+'-'+branch
    return project_name


def nginx_user():
  """ Returns the correct apache user for the environment
  """
  return 'www-data'


def current_user():
  """ Returns the current user
  """
  return env.run('whoami', capture=True) if env.run == lrun else env.run('whoami')


def sudo_run(command,user=None):
  """ Run the command, this is a wrapper as sudo on localhost is not very reliable
  """
  if env.run is lrun:
    if user:
      return env.run('sudo -u ' + user + ' ' + command)
    else:
      return env.run('sudo ' + command)
  else:
    return sudo(command, user=user)


def chown(path,owner,group=None,recursive=False,sudo=False):
  """ Change ownership of path to owner
  """
  command='chown '
  if recursive:
    command += '-R'
  if owner is None:
    owner=env.user
  command += ' ' + owner
  if group:
    command += ':' + group
  if sudo:
    sudo_run(command + ' ' + path)
  else:
    env.run(command + ' ' + path)


def chmod(path,mode,recursive=False,sudo=False):
  """ Change mode of path to mode
  """
  command = 'chmod '
  if recursive:
    command += '-R'
  command += ' ' + str(mode) + ' ' + path
  if sudo:
    sudo_run(command)
  else:
    env.run(command)


def unlink(path,sudo=False,recursive=False,force=False):
  """ Remove file path
  """
  command = 'rm '
  if recursive is not False:
    command += '-r '
  if force is not False:
    command += '-f '
  if sudo is False:
    env.run(command + path)
  else:
    if recursive is not False:
      yes = prompt('Are you sure you want to sudo run ' + command + path, default='n')
      if yes.lower()=='y':
        sudo_run(command + path)
    else:
      sudo_run(command + path)


def symlink(src, link, sudo = False, replace = True):
  """ Create a symlink [link] to [src]
  """
  command = 'ln -s '
  if replace is not False:
    command += '-f '
  if sudo:
    sudo_run(command + src + ' ' + link)
  else:
    env.run(command + src + ' ' + link)


@task
def localhost():
  """ Run command on localhost """
  env.run = lrun
  env.cd = lcd
  env.hosts = ["localhost"]


@task
def remote(host):
  """ Run command on remote hosts """
  env.run = run
  env.cd = cd
  if ',' in host:
    host = host.split(',')
  elif ' ' in host:
    host = host.split();
  else:
    host = [host]
  env.hosts = host


@task
def set_appperms_live(sitedir):
  """ Makes any changes to permissions required after deploy
  """
  chmod(path=sitedir,mode=755,recursive=True,sudo=True)
  chown(path=sitedir,owner='root',group=nginx_user(),recursive=True,sudo=True)


@task
def git_archive(branch='master', out='/tmp/outfile.zip'):
    """ RUN: "git archive [branch] -o [out (default '/tmp/outfile.zip')]" """
    # archive the git branch
    local("git archive " + branch + " -o " + out)


@task
def compile_and_checkin_rails_production_assets_locally():
  with settings(warn_only=True):
    local("RAILS_ENV=production bundle exec rake assets:precompile")
    local("git add .")
    local("git commit -a -m 'Adding compiled production assets for deployment'")


@task
def files_sync_from_remote(src=None,dst=None,user=None,delete=False):
  if src is None:
    src = prompt('Enter source path: ')
  if src is None:
    abort('Remote source path missing: ')
  if dst is None:
    dst = prompt('Enter destination path: ')
  if user is None:
    user = env.user
  d = ''
  if delete is True:
    d = ' --delete'
  env.run('rsync -r -a -v -e "ssh -l ' + user + '" ' + d + ' ' + src + ' ' + dst)


@task
def nginx_restart():
  """ Restart nginx
  """
  cmd = 'service nginx restart'
  sudo_run(cmd)


@task
def app_restart():
  """ Restart foreman
  """
  cmd = 'service ' + service_name + ' restart'
  sudo_run(cmd)


@task
def app_stop():
  """ Restart foreman
  """
  cmd = 'service ' + service_name + ' stop'
  sudo_run(cmd)


@task
def app_start():
  """ Restart foreman
  """
  cmd = 'service ' + service_name + ' start'
  sudo_run(cmd)


@task
def get_environment():
    return env.run('hostname')


def symlink_env_files():
  sudo_run('ln -s ' + '/etc/' + site_name + '/env-variables.conf ' + sitedir + '/.env')

def symlink_files_dir():
  sudo_run('ln -s ' + files_dir + ' ' + sitedir + '/public/system')

@task
def deploy(branch='master', debug=False):
  """ Deploy the site to server specified by remote/local
  """
  output['running'] = False
  output['stdout'] = False

  if debug:
    output['running'] = True
    output['stdout'] = True

  environment = get_environment()
  puts(green("Host is : ") + yellow(environment))

  # This particular project, we do it this way.
  puts(green("Compiling and checking in production assets locally."))
  compile_and_checkin_rails_production_assets_locally()

  puts(green("Generating site package"))
  project = get_project_name(branch)
  site_package = '/tmp/' + project + '.zip'

  puts(green("Package name : ") + yellow(project))
  site_dir = web_docs_dir + '/' + site_name

  puts(green("Archiving package"))
  git_archive(branch, site_package)

  puts(green("Copying package to remote server : ")+yellow(env.host))
  put(site_package, site_package)

  current_project_dir = release_dir + '/' + project
  puts(green("Uncompressing site package"))
  sudo_run('unzip -q -o -u '+site_package+' -d ' + current_project_dir)

  with settings(warn_only=True):
    puts(green("Shutting down app"))
    app_stop()

  puts(green("Removing link to previous release"))
  unlink(site_dir, True, force=True)

  puts(green("Linking site to new release"))
  symlink(current_project_dir, site_dir, True, True)

  puts(green("Symlinking .env file"))
  symlink_env_files()

  puts(green("Symlinking files directory"))
  symlink_files_dir()

  # set the ownership of the just deployed package
  puts(green("Setting permissions for prduction environment"))
  set_appperms_live(site_dir)

  with cd(sitedir):
    puts(green("Bundle updating"))
    sudo_run('bundle')

    puts(green("Running migrations"))
    sudo_run('RAILS_ENV=production bundle exec rake db:migrate')

    # Only the first time
    # puts(green("Seeding initial data"))
    # sudo_run('RAILS_ENV=production bundle exec rake db:seed')

    puts(green("Clearing cache"))
    sudo_run('RAILS_ENV=production bundle exec rake tmp:cache:clear')

    puts(green("Rebuilding tmp"))
    sudo_run('RAILS_ENV=production bundle exec rake tmp:create')

    # Not for this project - commit compiled assets to git on local.
    # puts(green("Compiling static assets"))
    # sudo_run('RAILS_ENV=production bundle exec rake assets:precompile')

    # Generally avoid this via -d /full/path
    puts(green("Rebuilding upstart script"))
    sudo_run('foreman export --app ' + service_name + ' --user root upstart /etc/init')

  puts(green("Starting app back up"))
  app_start()

  # Restart
  puts(green("Restarting nginx"))
  nginx_restart()
