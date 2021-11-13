pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'suspended')

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: project_short_name + '.in',
  output: meson.project_name(),
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

suspended_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'app_manager.py',
  'suspender_manager.py',
  'conf_manager.py',
  'settings_view.py',
  'workspaces_view.py',
  'mode_switch.py',
  'app_obj.py',
  'utils.py',
  'upower_backend.py'
]

install_data(suspended_sources, install_dir: moduledir)
