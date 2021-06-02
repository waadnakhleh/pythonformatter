import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Haifa-Project-WaadNakhleh",
    version="0.0.1",
    author="Waad Nakhleh",
    author_email="waad.nakhleh@gmail.com",
    description="Python formatter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/waadnakhleh/pythonformatter",
    project_urls={
        "Bug Tracker": "https://github.com/waadnakhleh/pythonformatter/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "lib"},
    packages=setuptools.find_packages(where="lib"),
    python_requires=">=3.8",
)