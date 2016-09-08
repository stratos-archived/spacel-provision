from setuptools import setup, find_packages

setup(name='spacel-provision',
      version='0.2.0',
      description='Space Elevator provisioner',
      long_description=open('README.md').read(),
      url='https://github.com/pebble/spacel-provision',
      author='Pebble WebOps',
      author_email='webops@pebble.com',
      license='MIT',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['test']),
      package_data={
          'spacel': [
              'cloudformation/*.template'
          ]
      },
      include_package_data=True,
      install_requires=open('requirements.txt').read().splitlines(),
      zip_safe=True)
