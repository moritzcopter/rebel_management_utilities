import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rebel_management_utilities",
    version="0.0.1",
    author="SamLubbers",
    author_email="samxr@protonmail.com",
    description="Utility functions for querying, cleaning and processing data of Extinction Rebellion members",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SamLubbers/rebel_management_utilities",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'python-dotenv'
        'requests'
    ]
)
