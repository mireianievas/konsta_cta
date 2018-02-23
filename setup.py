from setuptools import setup

setup(
    name='konsta_cta',
    version='0.0.1',
    description='Building up an analysis using ctapipe',
    author='Konstantin Pfrang',
    author_email='konstantin.pfrang@desy.de',
    packages=['konsta_cta'],
    scripts=[],
    install_requires=['numpy', 'scipy', 'scikit-learn', 'astropy', 'pandas',
                      'matplotlib', 'ctapipe']
)