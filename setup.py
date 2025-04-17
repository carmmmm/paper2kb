from setuptools import setup, find_packages

setup(
    name="paper2kb",
    version="0.1.0",
    description="Extract gene-disease metadata from biomedical literature",
    author="Carmen Montero",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "biopython",
        "spacy",
        "pandas",
        "requests",
        "python-dotenv",
        "pyliftover",
    ],
    entry_points={
        'console_scripts': [
            'paper2kb = src.cli:main',  # refers to src/cli.py's main()
        ],
    },
    include_package_data=True,
    zip_safe=False,
)