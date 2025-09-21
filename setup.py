from setuptools import setup, find_packages

setup(
    name='steel_lib',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'forallpeople',
        'steelpy',
        'numba',
        'handcalcs',
    ],
    author='Kilo Code',
    author_email='',
    description='A Python library for steel connection design calculations.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/your_username/your_project_name',  # Replace with your project's URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)