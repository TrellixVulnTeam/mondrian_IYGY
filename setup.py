from setuptools import setup, find_packages
import versioneer


setup(
    name='mondrian',
    packages=find_packages(),
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='single cell dna workflows',
    author='Diljot Grewal',
    author_email='diljot.grewal@gmail.com',
    entry_points={'console_scripts': ['mondrian = mondrian.run:main']},
    package_data={'':['scripts/*.py', 'scripts/*.R', 'scripts/*.npz', "config/*.yaml", "data/*"]}
)
