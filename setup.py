from setuptools import setup, find_packages

setup(name='spacel-provision',
      version='0.0.1',
      description='Space Elevator provisioner',
      long_description=open('README.md').read(),
      url='https://github.com/pebble/spacel-provision',
      author='Pebble WebOps',
      author_email='webops_team@pebble.com',
      license='MIT',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['test']),
      install_requires=open('requirements.txt').read().splitlines(),
      zip_safe=True)
