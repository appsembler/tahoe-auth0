import setuptools

import tahoe_auth0

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="tahoe-auth0",
    version=tahoe_auth0.__version__,
    author="Appsembler",
    author_email="ops@appsembler.com",
    description="Django object management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/appsembler/tahoe-auth0",
    project_urls={
        "Bug Tracker": "https://github.com/appsembler/tahoe-auth0/issues",
    },
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
    ],
    python_requires=">=3.5",
    packages=setuptools.find_packages(
        include=["tahoe_auth0", "tahoe_auth0.*"],
        exclude=["tahoe_auth0.tests"],
    ),
)
