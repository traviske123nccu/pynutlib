from setuptools import setup

setup(
    name='pynutlib',
    version='0.1.0',
    py_modules=['pynut'],
    author='traviske123nccu',
    author_email='113351001@g.nccu.edu.tw',
    description='Nutrition scoring library using USDA API and Streamlit',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/traviske123nccu/pynutlib',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'streamlit',
        'requests',
        'pandas',
        'numpy',
        'matplotlib'
    ],
    python_requires='>=3.7',
)
