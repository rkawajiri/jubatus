import Options

VERSION = '0.4.0'
APPNAME = 'jubatus'

top = '.'
out = 'build'
subdirs = ['src', 'client', 'config']

def options(opt):
  opt.load('compiler_cxx')
  opt.load('unittest_gtest')
  opt.load('gnu_dirs')

  opt.add_option('--enable-debug',
                 action='store_true', default=False,
                 dest='debug', help='build for debug')

  opt.add_option('--enable-zookeeper',
                 action='store_true', default=False, # dest='nozk',
                 help='use ZooKeeper')

  opt.add_option('--enable-gcov',
                 action='store_true', default=False,
                 dest='gcov', help='only for debug')

  opt.add_option('--enable-zktest',
                 action='store_true', default=False, 
                 dest='zktest', help='zk should run in localhost:2181')

  opt.recurse(subdirs)

def configure(conf):
  conf.env.CXXFLAGS += ['-O2', '-Wall', '-g', '-pipe']

  conf.load('compiler_cxx')
  conf.load('unittest_gtest')
  conf.load('gnu_dirs')

  # Generate config.hpp
  conf.env.JUBATUS_PLUGIN_DIR = conf.env['LIBDIR'] + '/jubatus/plugin'
  conf.define('JUBATUS_VERSION', VERSION)
  conf.define('JUBATUS_APPNAME', APPNAME)
  conf.define('JUBATUS_PLUGIN_DIR', conf.env.JUBATUS_PLUGIN_DIR)
  conf.write_config_header('src/config.hpp', guard="JUBATUS_CONFIG_HPP_", remove=False)

  conf.check_cxx(lib = 'msgpack')
  conf.check_cxx(lib = 'jubatus_mpio')
  conf.check_cxx(lib = 'jubatus_msgpack-rpc')
  conf.check_cxx(lib = 'dl')

  conf.check_cfg(package = 'libglog', args = '--cflags --libs')
  
  conf.check_cfg(package = 'pficommon', args = '--cflags --libs')
  conf.check_cxx(header_name = 'pficommon/network/mprpc.h', use = 'MSGPACK')

  conf.check_cxx(header_name = 'unistd.h')
  conf.check_cxx(header_name = 'sys/types.h')
  conf.check_cxx(header_name = 'sys/wait.h')
  conf.check_cxx(header_name = 'sys/stat.h')
  conf.check_cxx(header_name = 'cxxabi.h')
  conf.check_cxx(header_name = 'sys/socket.h net/if.h')
  conf.check_cxx(header_name = 'sys/ioctl.h')
  conf.check_cxx(header_name = 'fcntl.h')
  conf.check_cxx(header_name = 'netinet/in.h')
  conf.check_cxx(header_name = 'arpa/inet.h')
  conf.check_cxx(header_name = 'dlfcn.h')

  if not Options.options.debug:
    conf.define('NDEBUG', 1)

  if Options.options.enable_zookeeper:
    if (conf.check_cxx(header_name = 'c-client-src/zookeeper.h',
                           define_name = 'HAVE_ZOOKEEPER_H',
                           mandatory = False)):
      conf.define('ZOOKEEPER_HEADER', 'c-client-src/zookeeper.h')
    else:
      conf.check_cxx(header_name = 'zookeeper/zookeeper.h',
                     define_name = 'HAVE_ZOOKEEPER_H',
                     errmsg = 'ZooKeeper c-binding is not found. Please install c-binding.',
                     mandatory = True)
      conf.define('ZOOKEEPER_HEADER', 'zookeeper/zookeeper.h')

    conf.check_cxx(lib = 'zookeeper_mt', errmsg = 'ZK not found')

    if Options.options.zktest:
      conf.env.INTEGRATION_TEST = True

  if Options.options.gcov:
    conf.env.append_value('CXXFLAGS', '-fprofile-arcs')
    conf.env.append_value('CXXFLAGS', '-ftest-coverage')
    conf.env.append_value('LINKFLAGS', '-lgcov')

  conf.define('BUILD_DIR',  conf.bldnode.abspath())

  conf.recurse(subdirs)

def build(bld):

  bld(source = 'jubatus.pc.in',
      prefix = bld.env['PREFIX'],
      exec_prefix = '${prefix}',
      libdir = bld.env['LIBDIR'],
      includedir = '${prefix}/include',
      PACKAGE = APPNAME,
      VERSION = VERSION)

  bld.recurse(subdirs)

def regenerate(ctx):
  import os
  server_node = ctx.path.find_node('src/server')
  mpidlconv_node = ctx.path.find_node('tools/mpidlconv')
  jenerator_node = ctx.path.find_node('tools/generator/jenerator')
  for idl_node in server_node.ant_glob('*.idl'):
    idl = idl_node.name
    service_name = os.path.splitext(idl)[0]
    ctx.cmd_and_log(['mpidl', 'cpp', idl, '-o', '.', '-p', '-n', 'jubatus'], cwd=server_node.abspath())
    ctx.cmd_and_log([mpidlconv_node.abspath(), '-I', '-i', '.', '-s', service_name], cwd=server_node.abspath())
    ctx.cmd_and_log([jenerator_node.abspath(), idl, '-o', '.', '-i', '-n', 'jubatus'], cwd=server_node.abspath())

def regenerate_client(ctx):
  import os
  server_node = ctx.path.find_node('src/server')
  client_node = ctx.path.find_node('client')
  mpidlconv_node = ctx.path.find_node('tools/mpidlconv')
  for idl_node in server_node.ant_glob('*.idl'):
    idl = idl_node.name
    service_name = os.path.splitext(idl)[0]
    ctx.cmd_and_log(['mpidl', 'cpp', idl, '-o', client_node.abspath(), '-p', '-n', 'jubatus::' + service_name], cwd=server_node.abspath())
    ctx.cmd_and_log([mpidlconv_node.abspath(), '-i', client_node.abspath(), '-s', service_name], cwd=server_node.abspath())
  for server_hpp in client_node.ant_glob('*_server.hpp'):
    server_hpp.delete()
