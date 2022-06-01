import setuptools

import tahoe_idp

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="tahoe-idp",
    version=tahoe_idp.__version__,
    author="Appsembler",
    author_email="ops@appsembler.com",
    description="Tahoe IdP user authentication package for Tahoe.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/appsembler/tahoe-idp",
    project_urls={
        "Bug Tracker": "https://github.com/appsembler/tahoe-idp/issues",
    },
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
    ],
    python_requires=">=3.5",
    packages=setuptools.find_packages(
        include=["tahoe_idp", "tahoe_idp.*"],
        exclude=["tahoe_idp.tests", "config", "registration", "templates"],
    ),
    entry_points={
        "lms.djangoapp": [
            "tahoe_idp = tahoe_idp.apps:TahoeIdpConfig",
        ],
        "cms.djangoapp": [
            "tahoe_idp = tahoe_idp.apps:TahoeIdpConfig",
        ],
    },
)
