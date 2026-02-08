# -*- coding: utf-8 -*-
"""
SysCRED - Système de Vérification de Crédibilité
=================================================
PhD Thesis Prototype - Neuro-Symbolic Credibility Verification

(c) Dominique S. Loyer
Citation Key: loyerModelingHybridSystem2025
"""

from setuptools import setup, find_packages

setup(
    name="syscred",
    version="2.0.0",
    author="Dominique S. Loyer",
    author_email="loyer.dominique_sebastien@courrier.uqam.ca",
    description="Neuro-Symbolic Credibility Verification System",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/DominiqueLoyer/syscred",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "rdflib>=6.0.0",
        "nltk>=3.7",
    ],
    extras_require={
        "ml": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
            "numpy>=1.23.0,<2.0",
        ],
        "ir": [
            "pyserini>=0.21.0",
            "pytrec_eval>=0.5",
        ],
        "web": [
            "flask>=2.0.0",
            "flask-cors>=3.0.0",
        ],
        "full": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
            "numpy>=1.23.0,<2.0",
            "pyserini>=0.21.0",
            "pytrec_eval>=0.5",
            "flask>=2.0.0",
            "flask-cors>=3.0.0",
            "lime>=0.2.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="credibility verification nlp ontology information-retrieval",
)
