pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'suspended')
gnome = import('gnome')

gnome.compile_resources('suspended',
  'suspended.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'suspended.in',
  output: 'suspended',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

suspended_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'app_manager.py',
  'conf_manager.py',
  'settings_view.py',
  'workspaces_view.py',
]

install_data(suspended_sources, install_dir: moduledir)
